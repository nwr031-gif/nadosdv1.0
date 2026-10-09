<template>
  <div class="reports-view">
    <el-card class="page-header">
      <template #header>
        <div class="header-flex">
          <h2>التقارير</h2>
          <div class="header-actions">
            <el-select v-model="selectedRun" placeholder="اختر تشغيل" style="width: 250px" @change="loadReport">
              <el-option v-for="r in runs" :key="r.id" :label="`${r.scenario_name} - ${formatDate(r.started_at)}`" :value="r.id" />
            </el-select>
            <el-button type="primary" @click="generateReport" :disabled="!selectedRun || generating" :loading="generating">
              <Download /> إنشاء تقرير
            </el-button>
            <el-button @click="refreshRuns">
              <Refresh /> تحديث
            </el-button>
          </div>
        </div>
      </template>
      
      <el-row :gutter="16">
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-value">{{ reportData?.simulation_info?.scenario_name || '-' }}</div>
            <div class="stat-label">اسم السيناريو</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-value">{{ reportData?.execution_status?.status || '-' }}</div>
            <div class="stat-label">الحالة</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-value">{{ reportData?.execution_status?.duration_seconds ? formatDuration(reportData.execution_status.duration_seconds) : '-' }}</div>
            <div class="stat-label">المدة</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>إحصائيات الملاحظات</h3>
            </template>
            <el-descriptions v-if="reportData?.observation_statistics" border :column="2">
              <el-descriptions-item label="إجمالي المولدة">{{ reportData.observation_statistics.total_generated }}</el-descriptions-item>
              <el-descriptions-item label="الصالحة">{{ reportData.observation_statistics.valid_count }}</el-descriptions-item>
              <el-descriptions-item label="المرفوضة">{{ reportData.observation_statistics.rejected_count }}</el-descriptions-item>
              <el-descriptions-item label="معدل الرفض">{{ (reportData.observation_statistics.rejection_rate * 100).toFixed(1) }}%</el-descriptions-item>
            </el-descriptions>
            <el-divider />
            <h4>حسب المستشعر</h4>
            <el-table :data="sensorStats" border stripe size="small" style="width: 100%">
              <el-table-column prop="sensor" label="المستشعر"></el-table-column>
              <el-table-column prop="total" label="إجمالي" width="80"></el-table-column>
              <el-table-column prop="valid" label="صالحة" width="80"></el-table-column>
              <el-table-column prop="missing" label="مفقودة" width="80"></el-table-column>
              <el-table-column prop="invalid" label="غير صالحة" width="80"></el-table-column>
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>ملخص التتبع</h3>
            </template>
            <el-descriptions v-if="reportData?.tracking_summary" border :column="2">
              <el-descriptions-item label="إجمالي المسارات">{{ reportData.tracking_summary.total_tracks }}</el-descriptions-item>
              <el-descriptions-item label="المسارات النشطة">{{ reportData.tracking_summary.active_tracks }}</el-descriptions-item>
              <el-descriptions-item label="المسارات المفقودة">{{ reportData.tracking_summary.lost_tracks }}</el-descriptions-item>
              <el-descriptions-item label="متوسط الملاحظات/مسار">{{ reportData.tracking_summary.average_observations_per_track.toFixed(1) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>الأخطاء والتحذيرات</h3>
            </template>
            <el-descriptions v-if="reportData?.errors_and_warnings" border :column="2">
              <el-descriptions-item label="الأخطاء">
                <el-tag type="danger">{{ reportData.errors_and_warnings.error_count }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="التحذيرات">
                <el-tag type="warning">{{ reportData.errors_and_warnings.warning_count }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="الحرجة">
                <el-tag type="danger" effect="dark">{{ reportData.errors_and_warnings.critical_count }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <h3>القيود المعروفة</h3>
            </template>
            <ul class="limitations-list" v-if="reportData?.known_limitations">
              <li v-for="lim in reportData.known_limitations" :key="lim">{{ lim }}</li>
            </ul>
          </el-card>
        </el-col>
      </el-row>

      <!-- Export Buttons -->
      <el-card style="margin-top: 16px">
        <template #header>
          <h3>تصدير التقرير</h3>
        </template>
        <div class="export-actions">
          <el-button type="primary" @click="exportJSON" :disabled="!reportData || exporting">
            <Download /> تصدير JSON
          </el-button>
          <el-button type="success" @click="exportCSV" :disabled="!reportData || exporting">
            <Document /> تصدير CSV
          </el-button>
        </div>
      </el-card>

      <!-- Run History -->
      <el-card style="margin-top: 16px">
        <template #header>
          <h3>تاريخ التشغيلات</h3>
        </template>
        <el-table :data="runs" border stripe style="width: 100%">
          <el-table-column prop="id" label="معرف التشغيل" width="180"></el-table-column>
          <el-table-column prop="scenario_name" label="السيناريو" width="200"></el-table-column>
          <el-table-column prop="status" label="الحالة" width="120">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)" size="small">{{ getStatusText(scope.row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="started_at" label="وقت البدء" width="180">
            <template #default="scope">{{ formatDate(scope.row.started_at) }}</template>
          </el-table-column>
          <el-table-column prop="duration" label="المدة (ث)" width="100"></el-table-column>
          <el-table-column prop="seed" label="بذرة العشوائية" width="120"></el-table-column>
          <el-table-column label="الإجراءات" width="150">
            <template #default="scope">
              <el-button size="small" type="primary" @click="loadReport(scope.row.id)">
                <View /> عرض
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download, Document, View } from '@element-plus/icons-vue'

const runs = ref([])
const selectedRun = ref('')
const reportData = ref(null)
const generating = ref(false)
const exporting = ref(false)

const statusTypes = {
  pending: 'info',
  running: 'danger',
  paused: 'warning',
  completed: 'success',
  failed: 'danger',
  cancelled: 'info'
}

const statusTexts = {
  pending: 'معلق',
  running: 'قيد التشغيل',
  paused: 'متوقف مؤقتاً',
  completed: 'مكتمل',
  failed: 'فاشل',
  cancelled: 'ملغي'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ar-EG', { hour12: false })
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

const getStatusType = (status) => statusTypes[status] || 'info'
const getStatusText = (status) => statusTexts[status] || status

const sensorStats = computed(() => {
  if (!reportData.value?.observation_statistics?.by_sensor) return []
  return Object.entries(reportData.value.observation_statistics.by_sensor).map(([sensor, stats]) => ({
    sensor,
    ...stats
  }))
})

const loadRuns = async () => {
  // Mock data
  runs.value = [
    { id: 'run_001', scenario_name: 'تتبع أساسي', status: 'completed', started_at: '2024-01-15T10:30:00Z', duration: 60, seed: 42 },
    { id: 'run_002', scenario_name: 'مستشعر ضوضائي', status: 'completed', started_at: '2024-01-15T11:00:00Z', duration: 120, seed: 12345 },
    { id: 'run_003', scenario_name: 'متعدد المستشعرات', status: 'completed', started_at: '2024-01-15T11:30:00Z', duration: 180, seed: 98765 }
  ]
}

const loadReport = async (runId) => {
  selectedRun.value = runId
  try {
    // Mock report data
    reportData.value = {
      simulation_info: {
        scenario_name: runs.value.find(r => r.id === runId)?.scenario_name || 'Unknown',
        scenario_schema_version: 'v1',
        random_seed: 42,
        simulation_duration_seconds: 60
      },
      execution_status: {
        status: 'completed',
        started_at: '2024-01-15T10:30:00Z',
        completed_at: '2024-01-15T10:31:00Z',
        duration_seconds: 60
      },
      observation_statistics: {
        total_generated: 600,
        valid_count: 580,
        rejected_count: 20,
        rejection_rate: 0.033,
        by_sensor: {
          'radar_001': { total: 300, valid: 290, missing: 10, invalid: 0 }
        }
      },
      tracking_summary: {
        total_tracks: 1,
        active_tracks: 1,
        lost_tracks: 0,
        average_observations_per_track: 290
      },
      errors_and_warnings: {
        error_count: 0,
        warning_count: 2,
        critical_count: 0
      },
      known_limitations: [
        'محاكاة تستخدم نماذج حركية مبسطة',
        'نماذج المستشعرات افتراضية وغير معاير لأنظمة حقيقية',
        'التتبع يستخدم مرشح كالمّان أساسي مع افتراض سرعة ثابتة',
        'الدمج يفترض أخطاء مستشعرات غير مترابطة',
        'لا توجد تأثيرات انتشار جوي مُحاكاة'
      ]
    }
    ElMessage.success('تم تحميل التقرير')
  } catch (error) {
    ElMessage.error(`فشل التحميل: ${error.message}`)
  }
}

const generateReport = async () => {
  if (!selectedRun.value) return
  generating.value = true
  try {
    await loadReport(selectedRun.value)
    ElMessage.success('تم إنشاء التقرير')
  } finally {
    generating.value = false
  }
}

const exportJSON = () => {
  if (!reportData.value) return
  exporting.value = true
  try {
    const blob = new Blob([JSON.stringify(reportData.value, null, 2)], { type: 'application/json' })
    downloadBlob(blob, `report_${selectedRun.value}.json`)
    ElMessage.success('تم تصدير JSON')
  } finally {
    exporting.value = false
  }
}

const exportCSV = () => {
  if (!reportData.value) return
  exporting.value = true
  try {
    // Flatten report data for CSV
    const flatten = (obj, prefix = '') => {
      let result = {}
      for (const [key, value] of Object.entries(obj)) {
        const newKey = prefix ? `${prefix}.${key}` : key
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          Object.assign(result, flatten(value, newKey))
        } else {
          result[newKey] = value
        }
      }
      return result
    }
    
    const flat = flatten(reportData.value)
    const headers = Object.keys(flat)
    const rows = [headers.join(','), Object.values(flat).map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')]
    const csv = rows.join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    downloadBlob(blob, `report_${selectedRun.value}.csv`)
    ElMessage.success('تم تصدير CSV')
  } finally {
    exporting.value = false
  }
}

const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const refreshRuns = () => {
  loadRuns()
  ElMessage.success('تم تحديث القائمة')
}

onMounted(() => {
  loadRuns()
})
</script>

<style scoped>
.reports-view {
  padding: 20px 0;
}

.header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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
  font-size: 24px;
  font-weight: 700;
  color: #e94560;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #aaa;
  margin-top: 8px;
}

.export-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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

.limitations-list {
  padding-right: 20px;
  color: #aaa;
  line-height: 1.8;
}

.limitations-list li {
  margin-bottom: 8px;
}
</style>