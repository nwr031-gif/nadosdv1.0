<template>
  <div class="tracking-view">
    <el-card class="page-header">
      <template #header>
        <div class="header-flex">
          <h2>تتبع الأجسام</h2>
          <div class="tracking-controls">
            <el-button type="primary" @click="initializeTracker" :disabled="trackingActive">
              <Refresh /> تهيئة المراقب
            </el-button>
            <el-button type="danger" @click="resetTracker" :disabled="!trackingActive">
              <DeleteFilled /> إعادة ضبط
            </el-button>
          </div>
        </div>
      </template>
      
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>إعدادات مرشح كالمّان</h3>
            </template>
            <el-form :model="kfConfig" label-width="180px" inline>
              <el-form-item label="نموذج الحركة">
                <el-select v-model="kfConfig.motion_model" style="width: 200px">
                  <el-option label="سرعة ثابتة (CV)" value="constant_velocity" />
                  <el-option label="تسارع ثابت (CA)" value="constant_acceleration" />
                </el-select>
              </el-form-item>
              <el-form-item label="ضوضاء العملية">
                <el-input-number v-model="kfConfig.process_noise" :precision="3" :min="0.001" :max="10" :step="0.01" style="width: 120px" />
              </el-form-item>
              <el-form-item label="مقياس ضوضاء القياس">
                <el-input-number v-model="kfConfig.measurement_noise_scale" :precision="2" :min="0.1" :max="10" :step="0.1" style="width: 120px" />
              </el-form-item>
              <el-form-item label="خطوات التتابع القصوى">
                <el-input-number v-model="kfConfig.coast_max_steps" :precision="0" :min="1" :max="100" style="width: 120px" />
              </el-form-item>
              <el-form-item label="عتبة البوابة (كا²)">
                <el-input-number v-model="kfConfig.gate_threshold" :precision="2" :min="1" :max="50" :step="0.1" style="width: 120px" />
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>إعدادات ربط البيانات</h3>
            </template>
            <el-form :model="assocConfig" label-width="180px" inline>
              <el-form-item label="خوارزمية الربط">
                <el-select v-model="assocConfig.algorithm" style="width: 200px">
                  <el-option label="أقرب جار (NN)" value="nearest_neighbor" />
                  <el-option label="JPDA (قريباً)" value="jpda" disabled />
                </el-select>
              </el-form-item>
              <el-form-item label="عتبة الربط">
                <el-input-number v-model="assocConfig.gate_threshold" :precision="2" :min="1" :max="50" :step="0.1" style="width: 120px" />
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header-flex">
                <h3>المسارات النشطة</h3>
                <el-tag :type="tracks.length > 0 ? 'success' : 'info'" size="small">
                  {{ tracks.length }} مسار
                </el-tag>
              </div>
            </template>
            <el-table :data="tracks" border stripe size="small" style="width: 100%" highlight-current-row>
              <el-table-column prop="id" label="المعرف" width="120" />
              <el-table-column prop="x" label="س (م)" width="100">
                <template #default="scope">{{ scope.row.x.toFixed(0) }}</template>
              </el-table-column>
              <el-table-column prop="y" label="ص (م)" width="100">
                <template #default="scope">{{ scope.row.y.toFixed(0) }}</template>
              </el-table-column>
              <el-table-column prop="vx" label="Vx (م/ث)" width="100">
                <template #default="scope">{{ scope.row.vx.toFixed(1) }}</template>
              </el-table-column>
              <el-table-column prop="vy" label="Vy (م/ث)" width="100">
                <template #default="scope">{{ scope.row.vy.toFixed(1) }}</template>
              </el-table-column>
              <el-table-column prop="obs_count" label="الملاحظات" width="90" />
              <el-table-column prop="status" label="الحالة" width="100">
                <template #default="scope">
                  <el-tag :type="getTrackStatusColor(scope.row.status)" size="small">{{ scope.row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="cov_trace" label="أثر التباين" width="110">
                <template #default="scope">{{ scope.row.cov_trace.toFixed(1) }}</template>
              </el-table-column>
            </el-table>
            <div v-if="tracks.length === 0" class="empty-state">لا توجد مسارات نشطة - شغل المحاكاة وفعّل المراقب</div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>إحصائيات التتبع</h3>
            </template>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-card class="stat-card">
                  <div class="stat-value">{{ totalTracks }}</div>
                  <div class="stat-label">إجمالي المسارات</div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card class="stat-card">
                  <div class="stat-value">{{ activeTracks }}</div>
                  <div class="stat-label">مسارات نشطة</div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card class="stat-card">
                  <div class="stat-value">{{ coastingTracks }}</div>
                  <div class="stat-label">مسارات تتابع</div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card class="stat-card">
                  <div class="stat-value">{{ lostTracks }}</div>
                  <div class="stat-label">مسارات مفقودة</div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card class="stat-card">
                  <div class="stat-value">{{ avgObsPerTrack.toFixed(1) }}</div>
                  <div class="stat-label">متوسط الملاحظات/مسار</div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card class="stat-card">
                  <div class="stat-value">{{ avgCovTrace.toFixed(1) }}</div>
                  <div class="stat-label">متوسط أثر التباين</div>
                </el-card>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
      </el-row>

      <!-- Track Details -->
      <el-card v-if="selectedTrack" class="detail-card" style="margin-top: 16px">
        <template #header>
          <div class="detail-header">
            <h3>تفاصيل المسار: {{ selectedTrack.id }}</h3>
            <el-button size="small" @click="selectedTrack = null" circle><Close /></el-button>
          </div>
        </template>
        <el-descriptions border :column="3">
          <el-descriptions-item label="المعرف">{{ selectedTrack.id }}</el-descriptions-item>
          <el-descriptions-item label="الحالة">
            <el-tag :type="getTrackStatusColor(selectedTrack.status)">{{ selectedTrack.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="الموقع (س، ص، ع)">{{ formatPosition(selectedTrack) }}</el-descriptions-item>
          <el-descriptions-item label="السرعة (Vx، Vy، Vz)">{{ formatVelocity(selectedTrack) }}</el-descriptions-item>
          <el-descriptions-item label="عدد الملاحظات">{{ selectedTrack.obs_count }}</el-descriptions-item>
          <el-descriptions-item label="مصفوفة التباين (قطري)">{{ formatCovariance(selectedTrack) }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, DeleteFilled, Close } from '@element-plus/icons-vue'

const trackingActive = ref(false)
const selectedTrack = ref(null)

const kfConfig = reactive({
  motion_model: 'constant_velocity',
  process_noise: 0.1,
  measurement_noise_scale: 1.0,
  coast_max_steps: 10,
  gate_threshold: 9.21
})

const assocConfig = reactive({
  algorithm: 'nearest_neighbor',
  gate_threshold: 9.21
})

// Mock tracks data
const tracks = ref([
  { id: 'track_0001', x: 12500, y: 45000, z: 9800, vx: 248.5, vy: -12.3, vz: 0.5, obs_count: 45, status: 'active', cov_trace: 234.5 },
  { id: 'track_0002', x: -8200, y: 32000, z: 5100, vx: -156.2, vy: 89.7, vz: -1.2, obs_count: 32, status: 'active', cov_trace: 412.8 },
  { id: 'track_0003', x: 25000, y: -15000, z: 12000, vx: 89.4, vy: -210.5, vz: 3.1, obs_count: 18, status: 'coasting', cov_trace: 856.3 },
  { id: 'track_0004', x: -30000, y: 40000, z: 8500, vx: 0, vy: 0, vz: 0, obs_count: 5, status: 'lost', cov_trace: 1245.7 }
])

const totalTracks = computed(() => tracks.value.length)
const activeTracks = computed(() => tracks.value.filter(t => t.status === 'active').length)
const coastingTracks = computed(() => tracks.value.filter(t => t.status === 'coasting').length)
const lostTracks = computed(() => tracks.value.filter(t => t.status === 'lost').length)
const avgObsPerTrack = computed(() => tracks.value.reduce((sum, t) => sum + t.obs_count, 0) / (tracks.value.length || 1))
const avgCovTrace = computed(() => tracks.value.reduce((sum, t) => sum + t.cov_trace, 0) / (tracks.value.length || 1))

const initializeTracker = () => {
  trackingActive.value = true
  ElMessage.success('تم تهيئة مراقب كالمّان')
}

const resetTracker = () => {
  trackingActive.value = false
  ElMessage.info('تم إعادة ضبط المراقب')
}

const getTrackStatusColor = (status) => {
  const colors = { active: 'success', coasting: 'warning', lost: 'danger', terminated: 'info', initializing: 'info' }
  return colors[status] || 'info'
}

const formatPosition = (track) => `(${track.x.toFixed(0)}, ${track.y.toFixed(0)}, ${track.z.toFixed(0)})`
const formatVelocity = (track) => `(${track.vx.toFixed(1)}, ${track.vy.toFixed(1)}, ${track.vz.toFixed(1)})`
const formatCovariance = (track) => `${track.cov_trace.toFixed(1)}`

const formatPosition2 = (track) => `(${track.x.toFixed(0)}, ${track.y.toFixed(0)}, ${track.z.toFixed(0)})`
</script>

<style scoped>
.tracking-view {
  padding: 20px 0;
}

:deep(.el-form-item__label) {
  color: #eaeaea;
}

:deep(.el-form-item__content) {
  flex: 1;
}

:deep(.el-select .el-input__inner) {
  color: #eaeaea;
}

:deep(.el-input__inner) {
  background: #1a1a2e;
  border-color: #0f3460;
  color: #eaeaea;
}

.stat-card {
  background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
  border: 1px solid #0f3460;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(233, 69, 96, 0.2);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #e94560;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #aaa;
  margin-top: 8px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-header h3 {
  margin: 0;
  color: #eaeaea;
}

:deep(.el-descriptions__label) {
  color: #aaa;
  font-weight: 500;
}

:deep(.el-descriptions__value) {
  color: #eaeaea;
}

:deep(.el-form-item__label) {
  color: #eaeaea;
}
</style>