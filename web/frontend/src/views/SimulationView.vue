<template>
  <div class="simulation-view">
    <!-- Toolbar -->
    <el-card class="toolbar-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-select v-model="scenarioSelect" placeholder="اختر سيناريو" @change="onScenarioChange" style="width: 100%">
            <el-option v-for="s in availableScenarios" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-col>
        <el-col :span="16" class="controls">
          <el-button-group>
            <el-button :type="simulationStore.isRunning ? 'success' : 'primary'" 
                       :disabled="simulationStore.isRunning" @click="startSimulation" size="large">
              <VideoPlay /> {{ simulationStore.isRunning ? 'جاري التشغيل' : 'تشغيل المحاكاة' }}
            </el-button>
            <el-button type="warning" :disabled="!simulationStore.isRunning" @click="pauseSimulation" size="large">
              <VideoPause /> إيقاف مؤقت
            </el-button>
            <el-button type="info" :disabled="!simulationStore.isPaused" @click="resumeSimulation" size="large">
              <Refresh /> استئناف
            </el-button>
            <el-button type="danger" :disabled="!simulationStore.canStop" @click="stopSimulation" size="large">
              <VideoPause /> إيقاف
            </el-button>
            <el-button type="default" :disabled="simulationStore.status === 'idle'" @click="resetSimulation" size="large">
              <RefreshRight /> إعادة ضبط
            </el-button>
          </el-button-group>
          
          <el-divider direction="vertical" />
          
          <div class="speed-control">
            <span class="speed-label">السرعة:</span>
            <el-slider v-model="simulationStore.simulationSpeed" :min="0.1" :max="10" :step="0.1" 
                       @change="onSpeedChange" style="width: 150px" show-tooltip format-tooltip="formatSpeed" />
            <span class="speed-value">{{ simulationStore.simulationSpeed.toFixed(1) }}x</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- Main Content -->
    <el-row :gutter="16">
      <!-- Map View -->
      <el-col :span="18">
        <el-card class="map-card">
          <template #header>
            <div class="map-header">
              <h3>المشهد ثنائي الأبعاد</h3>
              <div class="map-legend">
                <span class="legend-item"><span class="legend-dot sensor-dot"></span> مستشعر</span>
                <span class="legend-item"><span class="legend-dot object-dot"></span> جسم</span>
                <span class="legend-item"><span class="legend-dot track-dot"></span> مسار</span>
                <span class="legend-item"><span class="legend-line trail-line"></span> مسار تاريخي</span>
              </div>
            </div>
          </template>
          <div class="map-container" ref="mapContainer">
            <canvas ref="canvas" id="simulation-canvas"></canvas>
            <div class="simulation-label">محاكاة - SIMULATION</div>
            <div class="coordinates" v-if="mousePosition">
              إ: {{ mousePosition.x.toFixed(0) }}م، ش: {{ mousePosition.y.toFixed(0) }}م
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Sidebar -->
      <el-col :span="6">
        <!-- Status Panel -->
        <el-card class="sidebar-card">
          <template #header>
            <div class="panel-header">
              <h4>حالة المحاكاة</h4>
              <el-tag :type="getStatusType(simulationStore.status)" effect="dark" size="small">
                {{ getStatusText(simulationStore.status) }}
              </el-tag>
            </div>
          </template>
          <div class="status-info">
            <div class="info-row">
              <span class="label">الوقت:</span>
              <span class="value">{{ simulationStore.formattedTime }}</span>
            </div>
            <div class="info-row">
              <span class="label">المدة:</span>
              <span class="value">{{ (simulationStore.simulationDuration || 0).toFixed(1) }} ث</span>
            </div>
            <div class="info-row">
              <span class="label">التقدم:</span>
              <div class="progress-mini">
                <el-progress :percentage="simulationStore.progress" :stroke-width="8" color="#e94560" />
              </div>
            </div>
            <div class="info-row">
              <span class="label">السرعة:</span>
              <span class="value">{{ simulationStore.simulationSpeed.toFixed(1) }}x</span>
            </div>
            <el-divider />
            <div class="info-row">
              <span class="label">أجسام:</span>
              <span class="value">{{ Object.keys(simulationStore.objects).length }}</span>
            </div>
            <div class="info-row">
              <span class="label">مستشعرات:</span>
              <span class="value">{{ Object.keys(simulationStore.sensors).length }}</span>
            </div>
            <div class="info-row">
              <span class="label">مسارات:</span>
              <span class="value">{{ Object.keys(simulationStore.tracks).length }}</span>
            </div>
          </div>
        </el-card>

        <!-- Objects List -->
        <el-card class="sidebar-card">
          <template #header>
            <h4>الأجسام المكتشفة</h4>
          </template>
          <el-table :data="objectList" border stripe size="small" style="width: 100%" highlight-current-row @current-change="onObjectSelect">
            <el-table-column prop="id" label="المعرف" width="100" />
            <el-table-column prop="type" label="النوع" width="80">
              <template #default="scope">
                <el-tag :type="getObjectTypeColor(scope.row.type)" size="small">{{ scope.row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="x" label="س (م)" width="80">
              <template #default="scope">{{ scope.row.x.toFixed(0) }}</template>
            </el-table-column>
            <el-table-column prop="y" label="ص (م)" width="80">
              <template #default="scope">{{ scope.row.y.toFixed(0) }}</template>
            </el-table-column>
            <el-table-column prop="speed" label="السرعة (م/ث)" width="100">
              <template #default="scope">{{ scope.row.speed.toFixed(1) }}</template>
            </el-table-column>
          </el-table>
          <div v-if="objectList.length === 0" class="empty-state">لا توجد أجسام</div>
        </el-card>

        <!-- Selected Object Details -->
        <el-card v-if="simulationStore.selectedObject" class="sidebar-card">
          <template #header>
            <div class="panel-header">
              <h4>تفاصيل الجسم</h4>
              <el-button size="small" @click="simulationStore.clearSelection" circle><Close /></el-button>
            </div>
          </template>
          <div class="detail-grid">
            <div class="detail-row">
              <span class="detail-label">المعرف:</span>
              <span class="detail-value">{{ selectedObj.id }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">النوع:</span>
              <span class="detail-value">{{ selectedObj.type }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">الموقع (س، ص، ع):</span>
              <span class="detail-value">({{ selectedObj.x.toFixed(1) }}, {{ selectedObj.y.toFixed(1) }}, {{ selectedObj.z.toFixed(1) }})</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">السرعة (س، ص، ع):</span>
              <span class="detail-value">({{ selectedObj.vx.toFixed(1) }}, {{ selectedObj.vy.toFixed(1) }}, {{ selectedObj.vz.toFixed(1) }})</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">السرعة الكلية:</span>
              <span class="detail-value">{{ selectedObj.speed.toFixed(1) }} م/ث</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">الاتجاه:</span>
              <span class="detail-value">{{ selectedObj.heading.toFixed(1) }}°</span>
            </div>
          </div>
        </el-card>

        <!-- Tracks List -->
        <el-card class="sidebar-card">
          <template #header>
            <h4>المسارات النشطة</h4>
          </template>
          <el-table :data="trackList" border stripe size="small" style="width: 100%">
            <el-table-column prop="id" label="المعرف" width="100" />
            <el-table-column prop="x" label="س (م)" width="80">
              <template #default="scope">{{ scope.row.x.toFixed(0) }}</template>
            </el-table-column>
            <el-table-column prop="y" label="ص (م)" width="80">
              <template #default="scope">{{ scope.row.y.toFixed(0) }}</template>
            </el-table-column>
            <el-table-column prop="obsCount" label="الملاحظات" width="80" />
            <el-table-column prop="status" label="الحالة" width="100">
              <template #default="scope">
                <el-tag :type="getTrackStatusColor(scope.row.status)" size="small">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="trackList.length === 0" class="empty-state">لا توجد مسارات</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulationStore } from '@/stores/simulation'
import { ElMessage } from 'element-plus'
import { VideoPlay, VideoPause, Refresh, RefreshRight, ZoomIn, ZoomOut, Expand, FullScreen } from '@element-plus/icons-vue'

const router = useRouter()
const simulationStore = useSimulationStore()

const canvasRef = ref(null)
const containerRef = ref(null)
const mousePosition = ref(null)

const availableScenarios = ref([
  { id: 'basic_tracking', name: 'تتبع أساسي - جسم واحد بمستشعر نظيف' },
  { id: 'noisy_sensor', name: 'مستشعر ضوضائي - قياسات مع ضوضاء' },
  { id: 'multi_sensor_demo', name: 'متعدد المستشعرات - دمج بيانات من ثلاثة مستشعرات' }
])

const scenarioSelect = ref('')

const objectList = computed(() => {
  return Object.entries(simulationStore.objects).map(([id, obj]) => ({
    id,
    type: obj.type || 'generic',
    x: obj.position?.x || obj.x || 0,
    y: obj.position?.y || obj.y || 0,
    z: obj.position?.z || obj.z || 0,
    vx: obj.velocity?.x || obj.vx || 0,
    vy: obj.velocity?.y || obj.vy || 0,
    vz: obj.velocity?.z || obj.vz || 0,
    speed: Math.sqrt((obj.velocity?.x || obj.vx || 0)**2 + (obj.velocity?.y || obj.vy || 0)**2 + (obj.velocity?.z || obj.vz || 0)**2),
    heading: Math.atan2(obj.velocity?.y || obj.vy || 0, obj.velocity?.x || obj.vx || 0) * 180 / Math.PI
  }))
})

const trackList = computed(() => {
  return Object.entries(simulationStore.tracks).map(([id, track]) => ({
    id,
    x: track.estimated_position?.x || track.x || 0,
    y: track.estimated_position?.y || track.y || 0,
    obsCount: track.observation_count || 0,
    status: track.tracking_status || 'active'
  }))
})

const selectedObj = computed(() => {
  if (!simulationStore.selectedObject) return null
  return objectList.value.find(o => o.id === simulationStore.selectedObject)
})

const ctx = ref(null)
const animationFrame = ref(null)
const viewState = ref({
  centerX: 0,
  centerY: 0,
  scale: 0.005,
  dragging: false,
  lastMouse: null
})

const MAP_SCALE = 0.005 // meters to pixels

function initCanvas() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return
  
  const ctx2d = canvas.getContext('2d')
  ctx.value = ctx2d
  
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  
  canvas.addEventListener('mousedown', onMouseDown)
  canvas.addEventListener('mousemove', onMouseMove)
  canvas.addEventListener('mouseup', onMouseUp)
  canvas.addEventListener('wheel', onWheel)
  canvas.addEventListener('contextmenu', onRightClick)
  
  startRenderLoop()
}

function resizeCanvas() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return
  
  const rect = container.getBoundingClientRect()
  canvas.width = rect.width * window.devicePixelRatio
  canvas.height = rect.height * window.devicePixelRatio
  canvas.style.width = rect.width + 'px'
  canvas.style.height = rect.height + 'px'
  ctx.value.scale(window.devicePixelRatio, window.devicePixelRatio)
}

function worldToScreen(x, y) {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0 }
  
  const centerX = canvas.width / 2 / window.devicePixelRatio
  const centerY = canvas.height / 2 / window.devicePixelRatio
  const scale = viewState.value.scale
  
  return {
    x: centerX + (x - viewState.value.centerX) * scale,
    y: centerY - (y - viewState.value.centerY) * scale // Y inverted
  }
}

function screenToWorld(screenX, screenY) {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0 }
  
  const centerX = canvas.width / 2 / window.devicePixelRatio
  const centerY = canvas.height / 2 / window.devicePixelRatio
  const scale = viewState.value.scale
  
  return {
    x: viewState.value.centerX + (screenX - centerX) / scale,
    y: viewState.value.centerY - (screenY - centerY) / scale
  }
}

function render() {
  const canvas = canvasRef.value
  const ctx2d = ctx.value
  if (!canvas || !ctx2d) return
  
  const width = canvas.width / window.devicePixelRatio
  const height = canvas.height / window.devicePixelRatio
  
  // Clear
  ctx2d.fillStyle = '#0a0a1a'
  ctx2d.fillRect(0, 0, width, height)
  
  // Grid
  drawGrid(ctx2d, width, height)
  
  // Axes
  drawAxes(ctx2d, width, height)
  
  // Sensors
  drawSensors(ctx2d)
  
  // Objects
  drawObjects(ctx2d)
  
  // Tracks
  drawTracks(ctx2d)
  
  // Selection highlight
  if (simulationStore.selectedObject) {
    drawSelection(ctx2d)
  }
  
  // Scale label
  ctx2d.fillStyle = '#666'
  ctx2d.font = '12px monospace'
  ctx2d.fillText(`مقياس: 1px = ${(1/viewState.value.scale).toFixed(0)}م`, 10, 20)
  
  // Simulation label
  ctx2d.fillStyle = '#e94560'
  ctx2d.font = 'bold 14px "Noto Sans Arabic"'
  ctx2d.fillText('محاكاة - SIMULATION', width - 140, height - 10)
  
  animationFrame.value = requestAnimationFrame(render)
}

function drawGrid(ctx2d, width, height) {
  const scale = viewState.value.scale
  const gridSpacing = 10000 // 10km
  const screenSpacing = gridSpacing * scale
  
  if (screenSpacing < 20) return
  
  ctx2d.strokeStyle = '#1a1a3e'
  ctx2d.lineWidth = 1
  
  const leftWorld = -viewState.value.centerX / scale
  const rightWorld = (width - viewState.value.centerX) / scale
  const topWorld = -viewState.value.centerY / scale
  const bottomWorld = (height - viewState.value.centerY) / scale
  
  ctx2d.beginPath()
  
  // Vertical lines
  let x = Math.floor(leftWorld / gridSpacing) * gridSpacing
  while (x <= rightWorld) {
    const sx = worldToScreen(x, 0).x
    ctx2d.moveTo(sx, 0)
    ctx2d.lineTo(sx, height)
    x += gridSpacing
  }
  
  // Horizontal lines
  let y = Math.floor(topWorld / gridSpacing) * gridSpacing
  while (y <= bottomWorld) {
    const sy = worldToScreen(0, y).y
    ctx2d.moveTo(0, sy)
    ctx2d.lineTo(width, sy)
    y += gridSpacing
  }
  
  ctx2d.stroke()
}

function drawAxes(ctx2d, width, height) {
  ctx2d.strokeStyle = '#444'
  ctx2d.lineWidth = 2
  
  const sy = worldToScreen(0, 0).y
  ctx2d.beginPath()
  ctx2d.moveTo(0, sy)
  ctx2d.lineTo(width, sy)
  ctx2d.stroke()
  
  const sx = worldToScreen(0, 0).x
  ctx2d.beginPath()
  ctx2d.moveTo(sx, 0)
  ctx2d.lineTo(sx, height)
  ctx2d.stroke()
  
  // Labels
  ctx2d.fillStyle = '#888'
  ctx2d.font = '12px "Noto Sans Arabic"'
  ctx2d.fillText('شرق (E)', width - 40, sy - 10)
  ctx2d.fillText('شمال (N)', sx + 10, 20)
}

function drawSensors(ctx2d) {
  ctx2d.fillStyle = '#00ff00'
  ctx2d.strokeStyle = '#00aa00'
  ctx2d.lineWidth = 2
  
  for (const [id, sensor] of Object.entries(simulationStore.sensors)) {
    const pos = sensor.position || sensor
    if (!pos) continue
    
    const screen = worldToScreen(pos.x || pos.x, pos.y || pos.y)
    if (!screen) continue
    
    // Sensor circle
    ctx2d.beginPath()
    ctx2d.arc(screen.x, screen.y, 8, 0, Math.PI * 2)
    ctx2d.fill()
    ctx2d.stroke()
    
    // Label
    ctx2d.fillStyle = '#00ff00'
    ctx2d.font = '11px "Noto Sans Arabic"'
    ctx2d.fillText(id, screen.x + 12, screen.y + 4)
  }
}

function drawObjects(ctx2d) {
  ctx2d.fillStyle = '#ff0000'
  ctx2d.strokeStyle = '#aa0000'
  ctx2d.lineWidth = 2
  
  for (const [id, obj] of Object.entries(simulationStore.objects)) {
    const pos = obj.position || obj
    const vel = obj.velocity || obj
    if (!pos) continue
    
    const screen = worldToScreen(pos.x || pos.x, pos.y || pos.y)
    if (!screen) continue
    
    // Trail
    if (obj.trail && obj.trail.length > 1) {
      ctx2d.strokeStyle = '#888888'
      ctx2d.lineWidth = 1
      ctx2d.beginPath()
      let first = true
      for (const p of obj.trail) {
        const s = worldToScreen(p.x, p.y)
        if (first) {
          ctx2d.moveTo(s.x, s.y)
          first = false
        } else {
          ctx2d.lineTo(s.x, s.y)
        }
      }
      ctx2d.stroke()
      ctx2d.strokeStyle = '#aa0000'
      ctx2d.lineWidth = 2
    }
    
    // Object triangle (pointing in velocity direction)
    const vx = vel.vx || vel.x || 0
    const vy = vel.vy || vel.y || 0
    const size = 12
    
    if (vx !== 0 || vy !== 0) {
      const angle = Math.atan2(vy, vx)
      const points = [
        { x: screen.x + size * Math.cos(angle), y: screen.y + size * Math.sin(angle) },
        { x: screen.x + size * Math.cos(angle + 2.5), y: screen.y + size * Math.sin(angle + 2.5) },
        { x: screen.x + size * Math.cos(angle - 2.5), y: screen.y + size * Math.sin(angle - 2.5) }
      ]
      
      ctx2d.beginPath()
      ctx2d.moveTo(points[0].x, points[0].y)
      ctx2d.lineTo(points[1].x, points[1].y)
      ctx2d.lineTo(points[2].x, points[2].y)
      ctx2d.closePath()
      ctx2d.fill()
      ctx2d.stroke()
    } else {
      ctx2d.beginPath()
      ctx2d.arc(screen.x, screen.y, 8, 0, Math.PI * 2)
      ctx2d.fill()
      ctx2d.stroke()
    }
    
    // Label
    ctx2d.fillStyle = '#ffaaaa'
    ctx2d.font = '11px "Noto Sans Arabic"'
    ctx2d.fillText(id, screen.x + 14, screen.y - 12)
  }
}

function drawTracks(ctx2d) {
  ctx2d.fillStyle = '#00ffff'
  ctx2d.strokeStyle = '#00aaaa'
  ctx2d.lineWidth = 2
  
  for (const [id, track] of Object.entries(simulationStore.tracks)) {
    const pos = track.estimated_position || track
    const cov = track.covariance_or_uncertainty
    if (!pos) continue
    
    const screen = worldToScreen(pos.x || pos.x, pos.y || pos.y)
    if (!screen) continue
    
    // Track square
    ctx2d.fillRect(screen.x - 6, screen.y - 6, 12, 12)
    ctx2d.strokeRect(screen.x - 6, screen.y - 6, 12, 12)
    
    // Uncertainty ellipse (simplified)
    if (cov) {
      const trace = (cov[0][0] || 0) + (cov[1][1] || 0)
      const radius = Math.sqrt(Math.max(0, trace)) * viewState.value.scale * 2
      if (radius > 2) {
        ctx2d.strokeStyle = '#0088aa'
        ctx2d.lineWidth = 1
        ctx2d.setLineDash([5, 5])
        ctx2d.beginPath()
        ctx2d.arc(screen.x, screen.y, radius, 0, Math.PI * 2)
        ctx2d.stroke()
        ctx2d.setLineDash([])
        ctx2d.strokeStyle = '#00aaaa'
        ctx2d.lineWidth = 2
      }
    }
    
    // Label
    ctx2d.fillStyle = '#aaffff'
    ctx2d.font = '11px "Noto Sans Arabic"'
    ctx2d.fillText(`T:${id}`, screen.x + 14, screen.y + 4)
  }
}

function drawSelection(ctx2d) {
  const obj = Object.entries(simulationStore.objects).find(([id]) => id === simulationStore.selectedObject)
  if (!obj) return
  
  const pos = obj[1].position || obj[1]
  if (!pos) return
  
  const screen = worldToScreen(pos.x || pos.x, pos.y || pos.y)
  if (!screen) return
  
  ctx2d.strokeStyle = '#ffff00'
  ctx2d.lineWidth = 3
  ctx2d.beginPath()
  ctx2d.arc(screen.x, screen.y, 15, 0, Math.PI * 2)
  ctx2d.stroke()
}

function startRenderLoop() {
  if (animationFrame.value) cancelAnimationFrame(animationFrame.value)
  render()
}

function onMouseDown(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  if (e.button === 0) { // Left click - pan
    viewState.value.dragging = true
    viewState.value.lastMouse = { x, y }
  } else if (e.button === 2) { // Right click - select object
    const world = screenToWorld(x, y)
    selectObjectAt(world.x, world.y)
  }
}

function onMouseMove(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  const world = screenToWorld(x, y)
  mousePosition.value = world
  
  if (viewState.value.dragging && viewState.value.lastMouse) {
    const dx = x - viewState.value.lastMouse.x
    const dy = y - viewState.value.lastMouse.y
    
    viewState.value.centerX -= dx / viewState.value.scale
    viewState.value.centerY += dy / viewState.value.scale // Y inverted
    
    viewState.value.lastMouse = { x, y }
  }
}

function onMouseUp() {
  viewState.value.dragging = false
  viewState.value.lastMouse = null
}

function onWheel(e) {
  e.preventDefault()
  const factor = e.deltaY > 0 ? 0.9 : 1.1
  viewState.value.scale *= factor
  viewState.value.scale = Math.max(0.0001, Math.min(0.01, viewState.value.scale))
}

function onRightClick(e) {
  e.preventDefault()
}

function selectObjectAt(worldX, worldY) {
  let minDist = Infinity
  let selected = null
  
  for (const [id, obj] of Object.entries(simulationStore.objects)) {
    const pos = obj.position || obj
    if (!pos) continue
    
    const dist = Math.sqrt((pos.x - worldX)**2 + (pos.y - worldY)**2)
    if (dist < minDist && dist < 50000) {
      minDist = dist
      selected = id
    }
  }
  
  if (selected) {
    simulationStore.selectObject(selected)
  } else {
    simulationStore.clearSelection()
  }
}

function onScenarioChange(value) {
  if (value) {
    loadScenario(value)
  }
}

async function loadScenario(scenarioId) {
  try {
    await simulationStore.loadScenario(scenarioId)
    ElMessage.success('تم تحميل السيناريو')
    // Reset view
    viewState.value.centerX = 0
    viewState.value.centerY = 0
  } catch (error) {
    ElMessage.error(`فشل التحميل: ${error.message}`)
  }
}

async function startSimulation() {
  try {
    await simulationStore.startSimulation()
    ElMessage.success('تم بدء المحاكاة')
  } catch (error) {
    ElMessage.error(`فشل التشغيل: ${error.message}`)
  }
}

function pauseSimulation() {
  simulationStore.pauseSimulation()
  ElMessage.info('تم إيقاف المحاكاة مؤقتاً')
}

function resumeSimulation() {
  simulationStore.resumeSimulation()
  ElMessage.success('تم استئناف المحاكاة')
}

function stopSimulation() {
  simulationStore.stopSimulation()
  ElMessage.warning('تم إيقاف المحاكاة')
}

function resetSimulation() {
  simulationStore.resetSimulation()
  viewState.value.centerX = 0
  viewState.value.centerY = 0
  ElMessage.info('تم إعادة ضبط المحاكاة')
}

function onSpeedChange(value) {
  simulationStore.setSpeed(value)
}

function formatSpeed(value) {
  return `${value.toFixed(1)}x`
}

function getStatusType(status) {
  const types = {
    'running': 'danger',
    'paused': 'warning',
    'idle': 'success',
    'completed': 'success',
    'stopped': 'info',
    'error': 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    'running': 'قيد التشغيل',
    'paused': 'متوقف مؤقتاً',
    'idle': 'جاهز',
    'completed': 'مكتمل',
    'stopped': 'متوقف',
    'error': 'خطأ'
  }
  return texts[status] || status
}

function getObjectTypeColor(type) {
  const colors = {
    'generic': 'info',
    'vehicle': 'primary',
    'projectile': 'warning',
    'target': 'danger',
    'decoy': 'info',
    'unknown': 'info'
  }
  return colors[type] || 'info'
}

function getTrackStatusColor(status) {
  const colors = {
    'active': 'success',
    'coasting': 'warning',
    'lost': 'danger',
    'terminated': 'info',
    'initializing': 'info'
  }
  return colors[status] || 'info'
}

function onObjectSelect(currentRow) {
  if (currentRow) {
    simulationStore.selectObject(currentRow.id)
  }
}

onMounted(() => {
  initCanvas()
  simulationStore.startPolling(500)
  watch(() => simulationStore.objects, () => {}, { deep: true })
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCanvas)
  if (animationFrame.value) cancelAnimationFrame(animationFrame.value)
  simulationStore.stopPolling()
})
</script>

<style scoped>
.simulation-view {
  height: calc(100vh - 140px);
  overflow: hidden;
}

.toolbar-card {
  margin-bottom: 16px;
}

.controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.speed-label {
  font-size: 13px;
  color: #aaa;
  white-space: nowrap;
}

.speed-value {
  font-family: monospace;
  font-weight: 600;
  color: #e94560;
  min-width: 50px;
}

.map-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.map-header h3 {
  margin: 0;
  color: #eaeaea;
}

.map-legend {
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: #aaa;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.sensor-dot { background: #00ff00; }
.legend-dot.object-dot { background: #ff0000; }
.legend-dot.track-dot { background: #00ffff; }

.legend-line {
  width: 20px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #888);
}

.map-container {
  position: relative;
  flex: 1;
  background: #0a0a1a;
  border-radius: 8px;
  overflow: hidden;
}

#simulation-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.coordinates {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  padding: 4px 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  color: #00ffff;
  pointer-events: none;
}

.sidebar-card {
  margin-bottom: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel-header h4 {
  margin: 0;
  color: #eaeaea;
}

.status-info {
  font-size: 13px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: #aaa;
}

.info-row .value {
  font-weight: 600;
  color: #eaeaea;
  font-family: monospace;
}

.progress-mini {
  flex: 1;
  max-width: 120px;
}

.sidebar-card :deep(.el-table) {
  font-size: 12px;
}

.sidebar-card :deep(.el-table th) {
  background: #0f3460;
  color: #eaeaea;
  font-size: 11px;
}

.sidebar-card :deep(.el-table td) {
  color: #eaeaea;
  font-size: 11px;
}

.detail-grid {
  display: grid;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  color: #aaa;
  font-size: 12px;
}

.detail-value {
  font-weight: 600;
  color: #eaeaea;
  font-family: monospace;
  font-size: 12px;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .simulation-view {
    height: auto;
  }
}
</style>