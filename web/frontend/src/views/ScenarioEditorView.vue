<template>
  <div class="scenario-editor-view">
    <el-card class="page-header">
      <template #header>
        <div class="header-flex">
          <h2>{{ editingScenario ? 'تعديل السيناريو' : 'إنشاء سيناريو جديد' }}</h2>
          <div class="header-actions">
            <el-button @click="resetForm" :disabled="!dirty">
              <Refresh /> إعادة تعيين
            </el-button>
            <el-button type="danger" @click="deleteScenario" :disabled="!editingScenario" v-if="editingScenario">
              <DeleteFilled /> حذف
            </el-button>
            <el-button type="primary" @click="saveScenario" :disabled="saving" :loading="saving">
              <Download /> {{ editingScenario ? 'تحديث' : 'حفظ' }}
            </el-button>
          </div>
        </div>
      </template>
      
      <el-form :model="scenarioForm" :rules="scenarioRules" ref="scenarioFormRef" label-width="140px" class="scenario-form">
        <!-- Basic Info -->
        <el-card class="form-section">
          <template #header>
            <h3>معلومات أساسية</h3>
          </template>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="معرف السيناريو" prop="scenario_id">
                <el-input v-model="scenarioForm.scenario_id" placeholder="مثال: basic_tracking" :readonly="editingScenario" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="إصدار المخطط" prop="schema_version">
                <el-select v-model="scenarioForm.schema_version" style="width: 100%">
                  <el-option label="v1" value="v1" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="الاسم" prop="name">
                <el-input v-model="scenarioForm.name" placeholder="اسم السيناريو" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="المدة (ثواني)" prop="duration_seconds">
                <el-input-number v-model="scenarioForm.duration_seconds" :min="1" :max="3600" :step="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="خطوة الوقت (ثواني)" prop="timestep_seconds">
                <el-input-number v-model="scenarioForm.timestep_seconds" :min="0.01" :max="1.0" :step="0.01" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="بذرة العشوائية" prop="random_seed">
                <el-input-number v-model="scenarioForm.random_seed" :min="0" :max="2147483647" :step="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="نظام الإحداثيات" prop="coordinate_system">
                <el-select v-model="scenarioForm.coordinate_system" style="width: 100%">
                  <el-option label="ENU (شرق-شمال-أعلى)" value="ENU" />
                  <el-option label="ECEF" value="ECEF" />
                  <el-option label="LLA" value="LLA" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="الوصف" prop="description">
                <el-input v-model="scenarioForm.description" type="textarea" :rows="3" placeholder="وصف السيناريو..." />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- Virtual Objects -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <h3>الأجسام الافتراضية</h3>
              <el-button type="primary" size="small" @click="addObject">
                <Plus /> إضافة جسم
              </el-button>
            </div>
          </template>
          
          <el-table :data="scenarioForm.virtual_objects" border stripe style="width: 100%" row-key="id">
            <el-table-column prop="object_id" label="المعرف" width="120" />
            <el-table-column prop="object_type" label="النوع" width="120">
              <template #default="scope">
                <el-tag size="small" :type="getObjectTypeColor(scope.row.object_type)">{{ scope.row.object_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="الموقع الابتدائي (س، ص، ع)" width="220">
              <template #default="scope">
                {{ formatVector(scope.row.initial_position) }}
              </template>
            </el-table-column>
            <el-table-column label="السرعة الابتدائية (س، ص، ع)" width="220">
              <template #default="scope">
                {{ formatVector(scope.row.initial_velocity) }}
              </template>
            </el-table-column>
            <el-table-column label="التسارع الابتدائي (س، ص، ع)" width="220">
              <template #default="scope">
                {{ formatVector(scope.row.initial_acceleration) }}
              </template>
            </el-table-column>
            <el-table-column prop="simulation_enabled" label="مفعل" width="80">
              <template #default="scope">
                <el-switch v-model="scope.row.simulation_enabled" active-text="نعم" inactive-text="لا" />
              </template>
            </el-table-column>
            <el-table-column label="الإجراءات" width="120">
              <template #default="scope">
                <el-button size="small" @click="editObject(scope.row, scope.$index)" link>
                  <Edit />
                </el-button>
                <el-button size="small" type="danger" @click="removeObject(scope.$index)" link>
                  <Delete />
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- Sensors -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <h3>المستشعرات الافتراضية</h3>
              <el-button type="primary" size="small" @click="addSensor">
                <Plus /> إضافة مستشعر
              </el-button>
            </div>
          </template>
          
          <el-table :data="scenarioForm.simulated_sensors" border stripe style="width: 100%" row-key="id">
            <el-table-column prop="sensor_id" label="المعرف" width="150" />
            <el-table-column prop="sensor_type" label="النوع" width="120">
              <template #default="scope">
                <el-tag size="small" :type="getSensorTypeColor(scope.row.sensor_type)">{{ scope.row.sensor_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="الموقع (س، ص، ع)" width="200">
              <template #default="scope">
                {{ formatVector(scope.row.simulated_position) }}
              </template>
            </el-table-column>
            <el-table-column prop="sampling_interval" label="فاصل العينات (ث)" width="130" />
            <el-table-column label="ضوضاء القياس" width="180">
              <template #default="scope">
                {{ formatMatrix(scope.row.measurement_noise) }}
              </template>
            </el-table-column>
            <el-table-column prop="active" label="مفعل" width="80">
              <template #default="scope">
                <el-switch v-model="scope.row.active" active-text="نعم" inactive-text="لا" />
              </template>
            </el-table-column>
            <el-table-column label="الإجراءات" width="120">
              <template #default="scope">
                <el-button size="small" @click="editSensor(scope.row, scope.$index)" link>
                  <Edit />
                </el-button>
                <el-button size="small" type="danger" @click="removeSensor(scope.$index)" link>
                  <Delete />
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- Environment & Visualization -->
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card class="form-section">
              <template #header>
                <h3>الظروف البيئية</h3>
              </template>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="الرياح س (م/ث)" prop="wind_x">
                    <el-input-number v-model="scenarioForm.environmental_conditions.wind_velocity.x" :precision="1" :step="0.1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="الرياح ص (م/ث)" prop="wind_y">
                    <el-input-number v-model="scenarioForm.environmental_conditions.wind_velocity.y" :precision="1" :step="0.1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="الرياح ع (م/ث)" prop="wind_z">
                    <el-input-number v-model="scenarioForm.environmental_conditions.wind_velocity.z" :precision="1" :step="0.1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="درجة الحرارة (°C)" prop="temperature">
                    <el-input-number v-model="scenarioForm.environmental_conditions.temperature_celsius" :precision="1" :step="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="الضغط (hPa)" prop="pressure">
                    <el-input-number v-model="scenarioForm.environmental_conditions.pressure_hpa" :precision="1" :step="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="الرطوبة (%)" prop="humidity">
                    <el-input-number v-model="scenarioForm.environmental_conditions.humidity_percent" :min="0" :max="100" :step="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="الرؤية (كم)" prop="visibility">
                    <el-input-number v-model="scenarioForm.environmental_conditions.visibility_km" :precision="1" :step="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="الهطول" prop="precipitation">
                    <el-select v-model="scenarioForm.environmental_conditions.precipitation" style="width: 100%">
                      <el-option label="لا يوجد" value="none" />
                      <el-option label="خفيف" value="light" />
                      <el-option label="معتدل" value="moderate" />
                      <el-option label="ثقيل" value="heavy" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="form-section">
              <template #header>
                <h3>إعدادات التصور</h3>
              </template>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="إظهار المسارات" prop="show_trails">
                    <el-switch v-model="scenarioForm.visualization_settings.show_trails" active-text="نعم" inactive-text="لا" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="طول المسار" prop="trail_length">
                    <el-input-number v-model="scenarioForm.visualization_settings.trail_length" :min="0" :max="10000" :step="10" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="إظهار عدم اليقين" prop="show_uncertainty">
                    <el-switch v-model="scenarioForm.visualization_settings.show_uncertainty_ellipses" active-text="نعم" inactive-text="لا" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="إظهار مجال رؤية المستشعر" prop="show_fov">
                    <el-switch v-model="scenarioForm.visualization_settings.show_sensor_fov" active-text="نعم" inactive-text="لا" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="مركز الخريطة س (م)" prop="map_center_x">
                    <el-input-number v-model="scenarioForm.visualization_settings.map_center.x" :precision="0" :step="1000" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="مركز الخريطة ص (م)" prop="map_center_y">
                    <el-input-number v-model="scenarioForm.visualization_settings.map_center.y" :precision="0" :step="1000" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="مدى الخريطة (كم)" prop="map_range">
                    <el-input-number v-model="scenarioForm.visualization_settings.map_range_km" :min="1" :max="10000" :step="10" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="لون الخلفية" prop="bg_color">
                    <el-color-picker v-model="scenarioForm.visualization_settings.background_color" show-alpha />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-card>
          </el-col>
        </el-row>

      <!-- Validation & Save -->
      <el-card>
        <div class="form-actions">
          <el-button @click="validateScenario" :icon="Checked" size="large">
            التحقق من السيناريو
          </el-button>
          <el-button type="primary" @click="saveScenario" :loading="saving" :disabled="saving">
            {{ editingScenario ? 'تحديث السيناريو' : 'حفظ السيناريو' }}
          </el-button>
          <el-button @click="exportScenario" :icon="Download">
            تصدير JSON
          </el-button>
          </div>
        </el-card>
      </el-form>
    </el-card>

    <!-- Object Dialog -->

    <!-- Object Dialog -->
    <el-dialog v-model="showObjectDialog" :title="editingObjectIndex > -1 ? 'تعديل الجسم' : 'إضافة جسم جديد'" width="700" destroy-on-close>
      <el-form :model="objectForm" :rules="objectRules" ref="objectFormRef" label-width="140px">
        <el-form-item label="المعرف" prop="object_id">
          <el-input v-model="objectForm.object_id" :readonly="editingObjectIndex > -1" />
        </el-form-item>
        <el-form-item label="النوع" prop="object_type">
          <el-select v-model="objectForm.object_type" style="width: 100%">
            <el-option label="عام" value="generic" />
            <el-option label="مركبة" value="vehicle" />
            <el-option label="مقذوف" value="projectile" />
            <el-option label="هدف" value="target" />
            <el-option label="خداع" value="decoy" />
            <el-option label="غير معروف" value="unknown" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="الموقع س" prop="pos_x"><el-input-number v-model="objectForm.initial_position.x" :precision="1" :step="100" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="الموقع ص" prop="pos_y"><el-input-number v-model="objectForm.initial_position.y" :precision="1" :step="100" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="الموقع ع" prop="pos_z"><el-input-number v-model="objectForm.initial_position.z" :precision="1" :step="100" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="السرعة س" prop="vel_x"><el-input-number v-model="objectForm.initial_velocity.x" :precision="1" :step="10" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="السرعة ص" prop="vel_y"><el-input-number v-model="objectForm.initial_velocity.y" :precision="1" :step="10" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="السرعة ع" prop="vel_z"><el-input-number v-model="objectForm.initial_velocity.z" :precision="1" :step="10" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="التسارع س" prop="acc_x"><el-input-number v-model="objectForm.initial_acceleration.x" :precision="1" :step="1" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="التسارع ص" prop="acc_y"><el-input-number v-model="objectForm.initial_acceleration.y" :precision="1" :step="1" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="التسارع ع" prop="acc_z"><el-input-number v-model="objectForm.initial_acceleration.z" :precision="1" :step="1" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="البعد س" prop="dim_x"><el-input-number v-model="objectForm.dimensions.x" :precision="1" :step="1" :min="0.1" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="البعد ص" prop="dim_y"><el-input-number v-model="objectForm.dimensions.y" :precision="1" :step="1" :min="0.1" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="البعد ع" prop="dim_z"><el-input-number v-model="objectForm.dimensions.z" :precision="1" :step="1" :min="0.1" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="نموذج الحركة" prop="motion_model">
          <el-select v-model="objectForm.motion_model" style="width: 100%">
            <el-option label="سرعة ثابتة" value="constant_velocity" />
            <el-option label="تسارع ثابت" value="constant_acceleration" />
          </el-select>
        </el-form-item>
        <el-form-item label="مفعل">
          <el-switch v-model="objectForm.simulation_enabled" active-text="نعم" inactive-text="لا" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showObjectDialog = false">إلغاء</el-button>
        <el-button type="primary" @click="submitObject">حفظ</el-button>
      </template>
    </el-dialog>

    <!-- Sensor Dialog -->
    <el-dialog v-model="showSensorDialog" :title="editingSensorIndex > -1 ? 'تعديل المستشعر' : 'إضافة مستشعر جديد'" width="600" destroy-on-close>
      <el-form :model="sensorForm" :rules="sensorRules" ref="sensorFormRef" label-width="140px">
        <el-form-item label="المعرف" prop="sensor_id">
          <el-input v-model="sensorForm.sensor_id" :readonly="editingSensorIndex > -1" />
        </el-form-item>
        <el-form-item label="النوع" prop="sensor_type">
          <el-select v-model="sensorForm.sensor_type" style="width: 100%">
            <el-option label="رادار" value="radar" />
            <el-option label="ليدار" value="lidar" />
            <el-option label="بصري" value="optical" />
            <el-option label="IRST" value="irst" />
            <el-option label="صوتي" value="acoustic" />
            <el-option label="عام" value="generic" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="الموقع س" prop="pos_x"><el-input-number v-model="sensorForm.simulated_position.x" :precision="0" :step="1000" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="الموقع ص" prop="pos_y"><el-input-number v-model="sensorForm.simulated_position.y" :precision="0" :step="1000" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="الموقع ع" prop="pos_z"><el-input-number v-model="sensorForm.simulated_position.z" :precision="0" :step="1000" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="فاصل العينات (ث)" prop="sampling_interval">
          <el-input-number v-model="sensorForm.sampling_interval" :precision="1" :min="0.01" :max="60" :step="0.1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="ضوضاء القياس (متر)" prop="noise">
          <el-input-number v-model="sensorForm.noise" :precision="0" :min="0" :max="10000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="احتمال التساقط" prop="dropout">
          <el-slider v-model="sensorForm.dropout" :min="0" :max="1" :step="0.01" show-input show-tooltip format-tooltip="formatPercent" />
        </el-form-item>
        <el-form-item label="مفعل">
          <el-switch v-model="sensorForm.active" active-text="نعم" inactive-text="لا" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSensorDialog = false">إلغاء</el-button>
        <el-button type="primary" @click="submitSensor">حفظ</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, DeleteFilled, Download, Checked, Refresh, Close } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const scenarioForm = reactive({
  scenario_id: '',
  schema_version: 'v1',
  name: '',
  description: '',
  duration_seconds: 60,
  timestep_seconds: 0.1,
  random_seed: 42,
  coordinate_system: 'ENU',
  virtual_objects: [],
  simulated_sensors: [],
  environmental_conditions: {
    wind_velocity: { x: 0, y: 0, z: 0 },
    temperature_celsius: 20,
    pressure_hpa: 1013.25,
    humidity_percent: 50,
    visibility_km: 10,
    precipitation: 'none'
  },
  visualization_settings: {
    show_trails: true,
    trail_length: 100,
    show_uncertainty_ellipses: true,
    show_sensor_fov: true,
    show_coordinates: true,
    map_center: { x: 0, y: 0, z: 0 },
    map_range_km: 100,
    background_color: '#1a1a2e',
    object_colors: {}
  }
})

const scenarioRules = {
  scenario_id: [{ required: true, message: 'يرجى إدخال المعرف', trigger: 'blur' }],
  name: [{ required: true, message: 'يرجى إدخال الاسم', trigger: 'blur' }],
  duration_seconds: [{ required: true, type: 'number', min: 1, message: 'مدة غير صالحة', trigger: 'blur' }],
  timestep_seconds: [{ required: true, type: 'number', min: 0.01, max: 1.0, message: 'خطوة وقت غير صالحة', trigger: 'blur' }],
  random_seed: [{ required: true, type: 'number', min: 0, message: 'بذرة غير صالحة', trigger: 'blur' }]
}

const scenarioFormRef = ref(null)

const showObjectDialog = ref(false)
const editingObjectIndex = ref(-1)
const objectForm = reactive({
  object_id: '',
  object_type: 'generic',
  initial_position: { x: 0, y: 0, z: 0 },
  initial_velocity: { x: 0, y: 0, z: 0 },
  initial_acceleration: { x: 0, y: 0, z: 0 },
  dimensions: { x: 10, y: 10, z: 5 },
  motion_model: 'constant_velocity',
  simulation_enabled: true
})

const objectRules = {
  object_id: [{ required: true, message: 'يرجى إدخال المعرف', trigger: 'blur' }],
  object_type: [{ required: true, message: 'يرجى اختيار النوع', trigger: 'change' }]
}

const objectFormRef = ref(null)

const showSensorDialog = ref(false)
const editingSensorIndex = ref(-1)
const sensorForm = reactive({
  sensor_id: '',
  sensor_type: 'radar',
  simulated_position: { x: 0, y: 0, z: 0 },
  sampling_interval: 1.0,
  noise: 100,
  dropout: 0.0,
  active: true
})

const sensorRules = {
  sensor_id: [{ required: true, message: 'يرجى إدخال المعرف', trigger: 'blur' }],
  sensor_type: [{ required: true, message: 'يرجى اختيار النوع', trigger: 'change' }],
  sampling_interval: [{ required: true, type: 'number', min: 0.01, message: 'فاصل عينات غير صالح', trigger: 'blur' }]
}

const sensorFormRef = ref(null)

const dirty = ref(false)
const saving = ref(false)

const formatVector = (v) => `(${v.x?.toFixed(1) || 0}, ${v.y?.toFixed(1) || 0}, ${v.z?.toFixed(1) || 0})`
const formatMatrix = (m) => m?.data ? `diag(${m.data[0][0]}, ${m.data[1][1]}, ${m.data[2][2]})` : 'غير محدد'
const formatPercent = (val) => `${(val * 100).toFixed(1)}%`

const getObjectTypeColor = (type) => {
  const colors = { generic: 'info', vehicle: 'primary', projectile: 'warning', target: 'danger', decoy: 'info', unknown: 'info' }
  return colors[type] || 'info'
}

const getSensorTypeColor = (type) => {
  const colors = { radar: 'primary', lidar: 'success', optical: 'warning', irst: 'warning', acoustic: 'info', generic: 'info' }
  return colors[type] || 'info'
}

const formatMatrixRow = (row) => row?.join(', ') || ''

const addObject = () => {
  editingObjectIndex.value = -1
  Object.assign(objectForm, {
    object_id: `obj_${scenarioForm.virtual_objects.length + 1}`,
    object_type: 'generic',
    initial_position: { x: 0, y: 0, z: 0 },
    initial_velocity: { x: 0, y: 0, z: 0 },
    initial_acceleration: { x: 0, y: 0, z: 0 },
    dimensions: { x: 10, y: 10, z: 5 },
    motion_model: 'constant_velocity',
    simulation_enabled: true
  })
  showObjectDialog.value = true
}

const editObject = (obj, index) => {
  editingObjectIndex.value = index
  Object.assign(objectForm, { ...obj })
  showObjectDialog.value = true
}

const removeObject = (index) => {
  ElMessageBox.confirm('هل تريد حذف هذا الجسم؟', 'تأكيد الحذف', {
    confirmButtonText: 'نعم',
    cancelButtonText: 'لا',
    type: 'warning'
  }).then(() => {
    scenarioForm.virtual_objects.splice(index, 1)
    dirty.value = true
    ElMessage.success('تم الحذف')
  })
}

const submitObject = () => {
  scenarioFormRef.value.validate((valid) => {
    if (valid) {
      const obj = {
        object_id: objectForm.object_id,
        object_type: objectForm.object_type,
        initial_position: { ...objectForm.initial_position },
        initial_velocity: { ...objectForm.initial_velocity },
        initial_acceleration: { ...objectForm.initial_acceleration },
        dimensions: { ...objectForm.dimensions },
        motion_model: objectForm.motion_model,
        simulation_enabled: objectForm.simulation_enabled
      }
      
      if (editingObjectIndex.value > -1) {
        scenarioForm.virtual_objects[editingObjectIndex.value] = obj
        ElMessage.success('تم تحديث الجسم')
      } else {
        scenarioForm.virtual_objects.push(obj)
        ElMessage.success('تم إضافة الجسم')
      }
      
      dirty.value = true
      showObjectDialog.value = false
      objectFormRef.value.resetFields()
    }
  })
}

const addSensor = () => {
  editingSensorIndex.value = -1
  Object.assign(sensorForm, {
    sensor_id: `sensor_${scenarioForm.simulated_sensors.length + 1}`,
    sensor_type: 'radar',
    simulated_position: { x: 0, y: 0, z: 0 },
    sampling_interval: 1.0,
    noise: 100,
    dropout: 0.0,
    active: true
  })
  showSensorDialog.value = true
}

const editSensor = (sensor, index) => {
  editingSensorIndex.value = index
  Object.assign(sensorForm, { 
    ...sensor,
    simulated_position: { ...sensor.simulated_position },
    measurement_noise: sensor.measurement_noise
  })
  showSensorDialog.value = true
}

const removeSensor = (index) => {
  ElMessageBox.confirm('هل تريد حذف هذا المستشعر؟', 'تأكيد الحذف', {
    confirmButtonText: 'نعم',
    cancelButtonText: 'لا',
    type: 'warning'
  }).then(() => {
    scenarioForm.simulated_sensors.splice(index, 1)
    dirty.value = true
    ElMessage.success('تم الحذف')
  })
}

const submitSensor = () => {
  sensorFormRef.value.validate((valid) => {
    if (valid) {
      const sensor = {
        sensor_id: sensorForm.sensor_id,
        sensor_type: sensorForm.sensor_type,
        simulated_position: { ...sensorForm.simulated_position },
        sampling_interval: sensorForm.sampling_interval,
        measurement_noise: {
          data: [
            [sensorForm.noise, 0, 0],
            [0, sensorForm.noise, 0],
            [0, 0, sensorForm.noise * 0.25]
          ]
        },
        availability_schedule: {},
        metadata: { dropout_probability: sensorForm.dropout },
        active: sensorForm.active
      }
      
      if (editingSensorIndex.value > -1) {
        scenarioForm.simulated_sensors[editingSensorIndex.value] = sensor
        ElMessage.success('تم تحديث المستشعر')
      } else {
        scenarioForm.simulated_sensors.push(sensor)
        ElMessage.success('تم إضافة المستشعر')
      }
      
      dirty.value = true
      showSensorDialog.value = false
      sensorFormRef.value.resetFields()
    }
  })
}

const validateScenario = () => {
  scenarioFormRef.value.validate((valid) => {
    if (valid) {
      // Additional validation
      const errors = []
      
      if (!scenarioForm.virtual_objects.length) {
        errors.push('يجب إضافة جسم افتراضي واحد على الأقل')
      }
      
      if (!scenarioForm.simulated_sensors.length) {
        errors.push('يجب إضافة مستشعر افتراضي واحد على الأقل')
      }
      
      const objectIds = new Set()
      for (const obj of scenarioForm.virtual_objects) {
        if (objectIds.has(obj.object_id)) {
          errors.push(`مكرر معرف الجسم: ${obj.object_id}`)
        }
        objectIds.add(obj.object_id)
      }
      
      const sensorIds = new Set()
      for (const sensor of scenarioForm.simulated_sensors) {
        if (sensorIds.has(sensor.sensor_id)) {
          errors.push(`مكرر معرف المستشعر: ${sensor.sensor_id}`)
        }
        sensorIds.add(sensor.sensor_id)
      }
      
      if (errors.length > 0) {
        ElMessageBox.alert(errors.join('\n'), 'أخطاء التحقق', {
          confirmButtonText: 'موافق',
          type: 'error'
        })
      } else {
        ElMessageBox.alert('السيناريو صالح وجاهز للتشغيل', 'نجاح التحقق', {
          confirmButtonText: 'موافق',
          type: 'success'
        })
      }
    }
  })
}

const saveScenario = async () => {
  scenarioFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        // In real app, call API
        await new Promise(resolve => setTimeout(resolve, 1000))
        dirty.value = false
        ElMessage.success(editingScenario ? 'تم تحديث السيناريو' : 'تم حفظ السيناريو')
      } catch (error) {
        ElMessage.error(`فشل الحفظ: ${error.message}`)
      } finally {
        saving.value = false
      }
    }
  })
}

const exportScenario = () => {
  const data = JSON.stringify(scenarioForm, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${scenarioForm.scenario_id || 'scenario'}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('تم التصدير')
}

const resetForm = () => {
  ElMessageBox.confirm('هل تريد إعادة تعيين النموذج؟ سيتم فقدان التغييرات غير المحفوظة.', 'تأكيد', {
    confirmButtonText: 'نعم',
    cancelButtonText: 'لا',
    type: 'warning'
  }).then(() => {
    scenarioFormRef.value.resetFields()
    // Reset to defaults
    Object.assign(scenarioForm, {
      scenario_id: '',
      schema_version: 'v1',
      name: '',
      description: '',
      duration_seconds: 60,
      timestep_seconds: 0.1,
      random_seed: 42,
      coordinate_system: 'ENU',
      virtual_objects: [],
      simulated_sensors: [],
      environmental_conditions: {
        wind_velocity: { x: 0, y: 0, z: 0 },
        temperature_celsius: 20,
        pressure_hpa: 1013.25,
        humidity_percent: 50,
        visibility_km: 10,
        precipitation: 'none'
      },
      visualization_settings: {
        show_trails: true,
        trail_length: 100,
        show_uncertainty_ellipses: true,
        show_sensor_fov: true,
        show_coordinates: true,
        map_center: { x: 0, y: 0, z: 0 },
        map_range_km: 100,
        background_color: '#1a1a2e',
        object_colors: {}
      }
    })
    dirty.value = false
    ElMessage.info('تم إعادة التعيين')
  })
}

const deleteScenario = () => {
  ElMessageBox.confirm('هل تريد حذف هذا السيناريو نهائياً؟', 'تأكيد الحذف', {
    confirmButtonText: 'نعم',
    cancelButtonText: 'لا',
    type: 'warning'
  }).then(() => {
    // In real app, call delete API
    ElMessage.success('تم الحذف')
    router.push('/scenario-editor')
  })
}
</script>

<style scoped>
.scenario-editor-view {
  padding: 20px 0;
}

.scenario-form {
  padding: 20px 0;
}

.form-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  color: #eaeaea;
}

:deep(.el-form-item__label) {
  color: #eaeaea;
}

:deep(.el-form-item__content) {
  flex: 1;
}

:deep(.el-input__inner) {
  background: #1a1a2e;
  border-color: #0f3460;
  color: #eaeaea;
}

:deep(.el-input__inner:focus) {
  border-color: #e94560;
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.2);
}

:deep(.el-select .el-input__inner) {
  color: #eaeaea;
}

:deep(.el-input-number__increase, .el-input-number__decrease) {
  color: #eaeaea;
}

:deep(.el-color-picker__trigger) {
  border-color: #0f3460;
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

.form-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding: 20px 0;
  border-top: 1px solid #0f3460;
  margin-top: 20px;
}

@media (max-width: 768px) {
  :deep(.el-form-item) {
    margin-bottom: 16px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .el-button {
    width: 100%;
  }
}
</style>