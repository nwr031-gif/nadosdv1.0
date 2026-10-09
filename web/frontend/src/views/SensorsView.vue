<template>
  <div class="sensors-view">
    <el-card class="page-header">
      <template #header>
        <div class="header-flex">
          <h2>المستشعرات الافتراضية</h2>
          <el-button type="primary" @click="showAddSensor = true">
            <Plus /> إضافة مستشعر
          </el-button>
        </div>
      </template>
      
      <el-table :data="sensors" border stripe style="width: 100%" highlight-current-row @current-change="onSensorSelect">
        <el-table-column prop="id" label="المعرف" width="150" />
        <el-table-column prop="type" label="النوع" width="120">
          <template #default="scope">
            <el-tag :type="getSensorTypeColor(scope.row.type)" size="small">{{ scope.row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="position" label="الموقع (س، ص، ع)" width="200">
          <template #default="scope">
            {{ formatPosition(scope.row.position) }}
          </template>
        </el-table-column>
        <el-table-column prop="sampling_interval" label="فاصل العينات (ث)" width="130" />
        <el-table-column prop="status" label="الحالة" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'" size="small">
              {{ scope.row.status === 'active' ? 'نشط' : 'غير نشط' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dropout" label="احتمال التساقط" width="120">
          <template #default="scope">
            {{ (scope.row.dropout * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column label="الإجراءات" width="180">
          <template #default="scope">
            <el-button size="small" @click="editSensor(scope.row)" link>
              <Edit />
            </el-button>
            <el-button size="small" type="danger" @click="deleteSensor(scope.row.id)" link>
              <Delete />
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Sensor Details Dialog -->
    <el-dialog v-model="showAddSensor" title="إضافة مستشعر جديد" width="600" destroy-on-close>
      <el-form :model="sensorForm" label-width="120px" :rules="sensorRules" ref="sensorFormRef">
        <el-form-item label="المعرف" prop="id">
          <el-input v-model="sensorForm.id" placeholder="مثال: radar_001" />
        </el-form-item>
        <el-form-item label="النوع" prop="type">
          <el-select v-model="sensorForm.type" placeholder="اختر النوع" style="width: 100%">
            <el-option label="رادار" value="radar" />
            <el-option label="ليدار" value="lidar" />
            <el-option label="بصري" value="optical" />
            <el-option label="IRST" value="irst" />
            <el-option label="صوتي" value="acoustic" />
            <el-option label="عام" value="generic" />
          </el-select>
        </el-form-item>
        <el-form-item label="الموقع س (م)" prop="x">
          <el-input-number v-model="sensorForm.x" :precision="0" :min="-1000000" :max="1000000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="الموقع ص (م)" prop="y">
          <el-input-number v-model="sensorForm.y" :precision="0" :min="-1000000" :max="1000000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="الموقع ع (م)" prop="z">
          <el-input-number v-model="sensorForm.z" :precision="0" :min="0" :max="50000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="فاصل العينات (ث)" prop="sampling_interval">
          <el-input-number v-model="sensorForm.sampling_interval" :precision="1" :min="0.01" :max="60" :step="0.1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="ضوضاء القياس (متر)" prop="noise">
          <el-input-number v-model="sensorForm.noise" :precision="0" :min="0" :max="10000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="احتمال التساقط" prop="dropout">
          <el-slider v-model="sensorForm.dropout" :min="0" :max="1" :step="0.01" show-input show-tooltip format-tooltip="formatPercent" />
        </el-form-item>
        <el-form-item label="الحالة">
          <el-switch v-model="sensorForm.active" active-text="نشط" inactive-text="غير نشط" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddSensor = false">إلغاء</el-button>
          <el-button type="primary" @click="submitSensor">حفظ</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Sensor Details Card -->
    <el-card v-if="selectedSensor" class="detail-card" style="margin-top: 20px">
      <template #header>
        <div class="detail-header">
          <h3>تفاصيل المستشعر: {{ selectedSensor.id }}</h3>
          <el-button size="small" @click="selectedSensor = null" circle><Close /></el-button>
        </div>
      </template>
      <el-descriptions border :column="2">
        <el-descriptions-item label="المعرف">{{ selectedSensor.id }}</el-descriptions-item>
        <el-descriptions-item label="النوع">
          <el-tag :type="getSensorTypeColor(selectedSensor.type)">{{ selectedSensor.type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="الموقع">{{ formatPosition(selectedSensor.position) }}</el-descriptions-item>
        <el-descriptions-item label="فاصل العينات">{{ selectedSensor.sampling_interval }} ث</el-descriptions-item>
        <el-descriptions-item label="ضوضاء القياس">{{ selectedSensor.noise }} متر</el-descriptions-item>
        <el-descriptions-item label="احتمال التساقط">{{ (selectedSensor.dropout * 100).toFixed(1) }}%</el-descriptions-item>
        <el-descriptions-item label="الحالة">
          <el-tag :type="selectedSensor.active ? 'success' : 'danger'">
            {{ selectedSensor.active ? 'نشط' : 'غير نشط' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Close } from '@element-plus/icons-vue'

const sensors = ref([
  { id: 'radar_north', type: 'radar', position: { x: 0, y: 0, z: 0 }, sampling_interval: 1.0, noise: 100, dropout: 0.05, active: true, status: 'active' },
  { id: 'radar_east', type: 'radar', position: { x: 50000, y: 0, z: 0 }, sampling_interval: 1.0, noise: 150, dropout: 0.03, active: true, status: 'active' },
  { id: 'lidar_south', type: 'lidar', position: { x: 0, y: -30000, z: 0 }, sampling_interval: 0.2, noise: 10, dropout: 0.01, active: true, status: 'active' }
])

const showAddSensor = ref(false)
const selectedSensor = ref(null)
const editingSensor = ref(null)

const sensorForm = reactive({
  id: '',
  type: 'radar',
  x: 0,
  y: 0,
  z: 0,
  sampling_interval: 1.0,
  noise: 100,
  dropout: 0.0,
  active: true
})

const sensorRules = {
  id: [{ required: true, message: 'يرجى إدخال المعرف', trigger: 'blur' }],
  type: [{ required: true, message: 'يرجى اختيار النوع', trigger: 'change' }],
  sampling_interval: [{ required: true, type: 'number', min: 0.01, message: 'فاصل عينات غير صالح', trigger: 'blur' }]
}

const sensorFormRef = ref(null)

const formatPosition = (pos) => {
  if (!pos) return 'غير محدد'
  return `(${pos.x || 0}, ${pos.y || 0}, ${pos.z || 0})`
}

const formatPercent = (val) => `${(val * 100).toFixed(1)}%`

const getSensorTypeColor = (type) => {
  const colors = { radar: 'primary', lidar: 'success', optical: 'warning', irst: 'warning', acoustic: 'info', generic: 'info' }
  return colors[type] || 'info'
}

const onSensorSelect = (currentRow) => {
  selectedSensor.value = currentRow
}

const showAddSensorDialog = () => {
  editingSensor.value = null
  Object.assign(sensorForm, {
    id: '',
    type: 'radar',
    x: 0,
    y: 0,
    z: 0,
    sampling_interval: 1.0,
    noise: 100,
    dropout: 0.0,
    active: true
  })
  showAddSensor.value = true
}

const editSensor = (sensor) => {
  editingSensor.value = sensor
  Object.assign(sensorForm, { ...sensor })
  showAddSensor.value = true
}

const submitSensor = () => {
  sensorFormRef.value.validate((valid) => {
    if (valid) {
      if (editingSensor.value) {
        // Update existing
        Object.assign(editingSensor.value, { ...sensorForm })
        ElMessage.success('تم تحديث المستشعر')
      } else {
        // Add new
        sensors.value.push({ ...sensorForm })
        ElMessage.success('تم إضافة المستشعر')
      }
      showAddSensor.value = false
      sensorFormRef.value.resetFields()
    }
  })
}

const deleteSensor = (id) => {
  ElMessageBox.confirm(`هل تريد حذف المستشعر ${id}؟`, 'تأكيد الحذف', {
    confirmButtonText: 'نعم',
    cancelButtonText: 'لا',
    type: 'warning'
  }).then(() => {
    const idx = sensors.value.findIndex(s => s.id === id)
    if (idx > -1) sensors.value.splice(idx, 1)
    ElMessage.success('تم حذف المستشعر')
    if (selectedSensor.value?.id === id) selectedSensor.value = null
  })
}
</script>

<style scoped>
.sensors-view {
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

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-form-item__label) {
  color: #eaeaea;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #0f3460;
  margin-top: 20px;
}

.detail-card {
  margin-top: 20px;
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
</style>