<template>
  <div class="tests-view">
    <el-card class="page-header">
      <template #header>
        <div class="header-flex">
          <h2>الاختبارات</h2>
          <div class="header-actions">
            <el-select v-model="testFilter" placeholder="جميع الأنواع" style="width: 180px">
              <el-option label="الكل" value="" />
              <el-option label="وحدة" value="unit" />
              <el-option label="تكامل" value="integration" />
              <el-option label="تراجع" value="regression" />
            </el-select>
            <el-button type="primary" @click="runTests" :disabled="running" :loading="running">
              <Refresh /> تشغيل الاختبارات
            </el-button>
            <el-button @click="refreshTests">
              <Refresh /> تحديث
            </el-button>
          </div>
        </div>
      </template>
      
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>ملخص الاختبارات</h3>
            </template>
            <el-row :gutter="16">
              <el-col :span="6">
                <el-card class="stat-card">
                  <div class="stat-value">{{ totalTests }}</div>
                  <div class="stat-label">إجمالي الاختبارات</div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card class="stat-card">
                  <div class="stat-value" style="color: #00ff00;">{{ passedTests }}</div>
                  <div class="stat-label">ناجحة</div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card class="stat-card">
                  <div class="stat-value" style="color: #ff0000;">{{ failedTests }}</div>
                  <div class="stat-label">فاشلة</div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card class="stat-card">
                  <div class="stat-value" style="color: #ffaa00;">{{ skippedTests }}</div>
                  <div class="stat-label">متخطاة</div>
                </el-card>
              </el-col>
            </el-row>
            <el-divider style="margin: 16px 0" />
            <el-row :gutter="16">
              <el-col :span="12">
                <el-card class="stat-card">
                  <div class="stat-value">{{ duration.toFixed(2) }} ث</div>
                  <div class="stat-label">مدة التشغيل</div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card class="stat-card">
                  <div class="stat-value">{{ coverage.toFixed(1) }}%</div>
                  <div class="stat-label">التغطية</div>
                </el-card>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>التغطية حسب الوحدة</h3>
            </template>
            <el-table :data="coverageData" border stripe size="small" style="width: 100%">
              <el-table-column prop="module" label="الوحدة" />
              <el-table-column prop="statements" label="العبارات %" width="120" />
              <el-table-column prop="branches" label="الفروع %" width="120" />
              <el-table-column prop="functions" label="الدوال %" width="120" />
              <el-table-column prop="lines" label="الأسطر %" width="120" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="24">
          <el-card>
            <template #header>
              <h3>نتائج الاختبارات التفصيلية</h3>
            </template>
            <el-table :data="testResults" border stripe style="width: 100%" highlight-current-row>
              <el-table-column prop="name" label="اسم الاختبار" min-width="300" />
              <el-table-column prop="type" label="النوع" width="100">
                <template #default="scope">
                  <el-tag :type="getTypeColor(scope.row.type)" size="small">{{ scope.row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="module" label="الوحدة" width="180" />
              <el-table-column prop="status" label="الحالة" width="100">
                <template #default="scope">
                  <el-tag :type="getStatusColor(scope.row.status)" size="small">{{ getStatusText(scope.row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="المدة (ث)" width="100" />
              <el-table-column prop="error" label="الخطأ" min-width="200" show-overflow-tooltip />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

const running = ref(false)
const testFilter = ref('')

const testResults = ref([
  { name: 'test_domain_models', type: 'unit', module: 'domain', status: 'passed', duration: 0.12, error: '' },
  { name: 'test_config_validation', type: 'unit', module: 'config', status: 'passed', duration: 0.08, error: '' },
  { name: 'test_motion_cv_predict', type: 'unit', module: 'motion', status: 'passed', duration: 0.15, error: '' },
  { name: 'test_motion_ca_predict', type: 'unit', module: 'motion', status: 'passed', duration: 0.18, error: '' },
  { name: 'test_radar_sensor', type: 'unit', module: 'sensors', status: 'passed', duration: 0.22, error: '' },
  { name: 'test_lidar_sensor', type: 'unit', module: 'sensors', status: 'passed', duration: 0.19, error: '' },
  { name: 'test_kalman_initialization', type: 'unit', module: 'tracking', status: 'passed', duration: 0.14, error: '' },
  { name: 'test_kalman_predict_update', type: 'unit', module: 'tracking', status: 'passed', duration: 0.25, error: '' },
  { name: 'test_kalman_gating', type: 'unit', module: 'tracking', status: 'passed', duration: 0.18, error: '' },
  { name: 'test_fusion_weighted_avg', type: 'unit', module: 'fusion', status: 'passed', duration: 0.16, error: '' },
  { name: 'test_fusion_covariance_intersection', type: 'unit', module: 'fusion', status: 'passed', duration: 0.22, error: '' },
  { name: 'test_persistence_scenario', type: 'integration', module: 'persistence', status: 'passed', duration: 0.45, error: '' },
  { name: 'test_persistence_run', type: 'integration', module: 'persistence', status: 'passed', duration: 0.52, error: '' },
  { name: 'test_scenario_execution', type: 'integration', module: 'orchestration', status: 'passed', duration: 1.25, error: '' },
  { name: 'test_kalman_numerical_regression', type: 'regression', module: 'tracking', status: 'passed', duration: 0.35, error: '' },
  { name: 'test_motion_numerical_regression', type: 'regression', module: 'motion', status: 'passed', duration: 0.28, error: '' },
  { name: 'test_fusion_numerical_regression', type: 'regression', module: 'fusion', status: 'passed', duration: 0.31, error: '' },
])

const totalTests = computed(() => testResults.value.length)
const passedTests = computed(() => testResults.value.filter(t => t.status === 'passed').length)
const failedTests = computed(() => testResults.value.filter(t => t.status === 'failed').length)
const skippedTests = computed(() => testResults.value.filter(t => t.status === 'skipped').length)
const duration = computed(() => testResults.value.reduce((sum, t) => sum + t.duration, 0))
const coverage = ref(87.5)

const coverageData = ref([
  { module: 'domain', statements: 96.5, branches: 92.0, functions: 98.0, lines: 95.8 },
  { module: 'config', statements: 94.2, branches: 89.5, functions: 95.0, lines: 93.7 },
  { module: 'motion', statements: 97.1, branches: 94.0, functions: 96.8, lines: 96.9 },
  { module: 'sensors', statements: 95.8, branches: 91.2, functions: 94.5, lines: 95.2 },
  { module: 'tracking', statements: 96.3, branches: 93.8, functions: 97.1, lines: 96.0 },
  { module: 'fusion', statements: 89.7, branches: 85.4, functions: 90.2, lines: 88.9 },
  { module: 'persistence', statements: 93.1, branches: 88.6, functions: 92.4, lines: 92.8 },
  { module: 'orchestration', statements: 91.5, branches: 87.3, functions: 90.8, lines: 90.9 },
  { module: 'reporting', statements: 88.9, branches: 84.2, functions: 89.5, lines: 88.3 },
])

const getTypeColor = (type) => {
  const colors = { unit: 'primary', integration: 'success', regression: 'warning' }
  return colors[type] || 'info'
}

const getStatusColor = (status) => {
  const colors = { passed: 'success', failed: 'danger', skipped: 'warning', error: 'danger' }
  return colors[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { passed: 'ناجح', failed: 'فاشل', skipped: 'متخطى', error: 'خطأ' }
  return texts[status] || status
}

const runTests = async () => {
  running.value = true
  ElMessage.info('جاري تشغيل الاختبارات...')
  
  // Simulate test run
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  running.value = false
  ElMessage.success('اكتملت الاختبارات بنجاح!')
}
</script>

<style scoped>
.tests-view {
  padding: 20px 0;
}

:deep(.el-table th) {
  background: #0f3460;
  color: #eaeaea;
}

:deep(.el-table td) {
  color: #eaeaea;
}

:deep(.el-table__row:hover > td) {
  background: rgba(233, 69, 96, 0.1);
}
</style>