<template>
  <div class="events-view">
    <el-card class="page-header">
      <template #header>
        <div class="header-flex">
          <h2>سجل الأحداث</h2>
          <div class="header-actions">
            <el-select v-model="severityFilter" placeholder="جميع المستويات" style="width: 160px" @change="applyFilters">
              <el-option label="الكل" value="" />
              <el-option label="معلومات" value="info" />
              <el-option label="تحذير" value="warning" />
              <el-option label="خطأ" value="error" />
              <el-option label="حرج" value="critical" />
            </el-select>
            <el-input v-model="searchQuery" placeholder="بحث..." size="small" style="width: 200px" @input="applyFilters" clearable />
            <el-button type="primary" @click="refreshEvents">
              <Refresh /> تحديث
            </el-button>
            <el-button @click="clearEvents">
              <DeleteFilled /> مسح السجل
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="filteredEvents" border stripe style="width: 100%" highlight-current-row default-sort="{ prop: 'timestamp', order: 'descending' }">
        <el-table-column prop="timestamp" label="الوقت" width="140" sortable>
          <template #default="scope">{{ formatTime(scope.row.timestamp) }}</template>
        </el-table-column>
        <el-table-column prop="severity" label="الخطورة" width="100" sortable>
          <template #default="scope">
            <el-tag :type="getSeverityType(scope.row.severity)" size="small" effect="dark">
              {{ getSeverityText(scope.row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="النوع" width="180" sortable />
        <el-table-column prop="source" label="المصدر" width="180" />
        <el-table-column prop="message" label="الرسالة" min-width="300" show-overflow-tooltip />
        <el-table-column prop="object_id" label="الجسم المرتبط" width="150" />
      </el-table>
      
      <div v-if="filteredEvents.length === 0" class="empty-state">
        لا توجد أحداث مطابقة للفلاتر
      </div>
      
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="totalEvents"
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="[20, 50, 100]"
        @current-change="fetchEvents"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, DeleteFilled } from '@element-plus/icons-vue'

const events = ref([])
const currentPage = ref(1)
const pageSize = ref(50)
const totalEvents = ref(0)
const severityFilter = ref('')
const searchQuery = ref('')
const loading = ref(false)

const severityTypes = {
  info: 'info',
  warning: 'warning',
  error: 'danger',
  critical: 'danger',
  debug: 'info'
}

const severityTexts = {
  info: 'معلومات',
  warning: 'تحذير',
  error: 'خطأ',
  critical: 'حرج',
  debug: 'تصحيح'
}

const eventTypes = [
  'scenario_started', 'scenario_paused', 'scenario_resumed', 'scenario_stopped',
  'scenario_reset', 'scenario_completed', 'object_created', 'object_destroyed',
  'observation_generated', 'observation_received', 'track_initialized',
  'track_updated', 'track_lost', 'track_terminated', 'fusion_performed',
  'sensor_status_changed', 'error_occurred', 'warning_issued', 'user_action', 'system_event'
]

const generateMockEvents = () => {
  const mockEvents = []
  const now = Date.now()
  for (let i = 0; i < 200; i++) {
    const type = eventTypes[Math.floor(Math.random() * eventTypes.length)]
    const severity = Object.keys(severityTypes)[Math.floor(Math.random() * Object.keys(severityTypes).length)]
    mockEvents.push({
      id: `evt_${i}`,
      timestamp: now - Math.random() * 86400000 * 7,
      severity,
      type,
      source: `nados.${['simulation', 'tracking', 'sensors', 'fusion', 'persistence'][Math.floor(Math.random() * 5)]}`,
      message: generateMessage(type, severity),
      object_id: Math.random() > 0.5 ? `target_${Math.floor(Math.random() * 5).toString().padStart(3, '0')}` : null
    })
  }
  return mockEvents.sort((a, b) => b.timestamp - a.timestamp)
}

const generateMessage = (type, severity) => {
  const messages = {
    scenario_started: 'تم بدء المحاكاة بنجاح',
    scenario_stopped: 'تم إيقاف المحاكاة',
    scenario_paused: 'تم إيقاف المحاكاة مؤقتاً',
    scenario_resumed: 'تم استئناف المحاكاة',
    object_created: 'تم إنشاء جسم افتراضي جديد',
    observation_generated: 'تم توليد ملاحظة من المستشعر',
    track_initialized: 'تم تهيئة مسار جديد',
    track_updated: 'تم تحديث المسار بملاحظة جديدة',
    track_lost: 'فُقد المسار بسبب عدم وجود ملاحظات',
    fusion_performed: 'تم دمج بيانات من مستشعرات متعددة',
    error_occurred: 'حدث خطأ في معالجة البيانات',
    warning_issued: 'تحذير: معدل التساقط مرتفع'
  }
  return messages[type] || `حدث ${type}`
}

const getSeverityType = (severity) => severityTypes[severity] || 'info'
const getSeverityText = (severity) => severityTexts[severity] || severity

const filteredEvents = computed(() => {
  let result = events.value
  
  if (severityFilter.value) {
    result = result.filter(e => e.severity === severityFilter.value)
  }
  
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(e => 
      e.message.toLowerCase().includes(q) ||
      e.type.toLowerCase().includes(q) ||
      e.source.toLowerCase().includes(q) ||
      (e.object_id && e.object_id.toLowerCase().includes(q))
    )
  }
  
  totalEvents.value = result.length
  return result.slice((currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value)
})

const formatTime = (ts) => {
  const date = new Date(ts)
  return date.toLocaleTimeString('ar-EG', { hour12: false }) + '.' + String(date.getMilliseconds()).padStart(3, '0')
}

const applyFilters = () => {
  currentPage.value = 1
}

const refreshEvents = () => {
  events.value = generateMockEvents()
  ElMessage.success('تم تحديث سجل الأحداث')
}

const clearEvents = () => {
  ElMessageBox.confirm('هل تريد مسح جميع الأحداث؟', 'تأكيد', {
    confirmButtonText: 'نعم',
    cancelButtonText: 'لا',
    type: 'warning'
  }).then(() => {
    events.value = []
    ElMessage.success('تم مسح السجل')
  })
}

const fetchEvents = () => {
  // In real app, fetch from API
}
</script>

<style scoped>
.events-view {
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