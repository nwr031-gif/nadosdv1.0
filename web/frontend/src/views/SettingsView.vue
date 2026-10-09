<template>
  <div class="settings-view">
    <el-card class="page-header">
      <h2>الإعدادات</h2>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card>
          <template #header>
            <h3>الإعدادات العامة</h3>
          </template>
          <el-form :model="generalSettings" label-width="120px">
            <el-form-item label="اللغة">
              <el-select v-model="generalSettings.language" style="width: 100%">
                <el-option label="العربية" value="ar" />
                <el-option label="English" value="en" />
              </el-select>
            </el-form-item>
            <el-form-item label="السمة">
              <el-select v-model="generalSettings.theme" style="width: 100%" @change="applyTheme">
                <el-option label="داكن" value="dark" />
                <el-option label="فاتح" value="light" />
              </el-select>
            </el-form-item>
            <el-form-item label="الوضع التجريبي">
              <el-switch v-model="generalSettings.debug" active-text="مفعل" inactive-text="معطل" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <h3>إعدادات المحاكاة</h3>
          </template>
          <el-form :model="simulationSettings" label-width="140px">
            <el-form-item label="بذرة العشوائية الافتراضية">
              <el-input-number v-model="simulationSettings.default_seed" :min="0" :max="2147483647" style="width: 100%" />
            </el-form-item>
            <el-form-item label="أقصى مدة (ثواني)">
              <el-input-number v-model="simulationSettings.max_duration" :min="1" :max="86400" style="width: 100%" />
            </el-form-item>
            <el-form-item label="أقصى عدد أجسام">
              <el-input-number v-model="simulationSettings.max_objects" :min="1" :max="10000" style="width: 100%" />
            </el-form-item>
            <el-form-item label="أقصى عدد مستشعرات">
              <el-input-number v-model="simulationSettings.max_sensors" :min="1" :max="500" style="width: 100%" />
            </el-form-item>
            <el-form-item label="أقصى ملاحظات لكل تشغيل">
              <el-input-number v-model="simulationSettings.max_observations" :min="100" :max="1000000" style="width: 100%" />
            </el-form-item>
            <el-form-item label="أقصى أحداث لكل تشغيل">
              <el-input-number v-model="simulationSettings.max_events" :min="100" :max="100000" style="width: 100%" />
            </el-form-item>
            <el-form-item label="خطوة الوقت الافتراضية">
              <el-input-number v-model="simulationSettings.default_timestep" :precision="2" :min="0.01" :max="1.0" :step="0.01" style="width: 100%" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <h3>قاعدة البيانات</h3>
          </template>
          <el-form :model="dbSettings" label-width="100px">
            <el-form-item label="مسار قاعدة البيانات">
              <el-input v-model="dbSettings.path" placeholder="data/nados.db" style="width: 100%" />
            </el-form-item>
            <el-form-item label="إظهار استعلامات SQL">
              <el-switch v-model="dbSettings.echo" active-text="نعم" inactive-text="لا" />
            </el-form-item>
            <el-form-item label="حجم مجموعة الاتصالات">
              <el-input-number v-model="dbSettings.pool_size" :min="1" :max="20" style="width: 100%" />
            </el-form-item>
            <el-form-item label="الحد الأقصى للاتصالات الإضافية">
              <el-input-number v-model="dbSettings.max_overflow" :min="0" :max="50" style="width: 100%" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="testDbConnection">
                <Connection /> اختبار الاتصال
              </el-button>
              <el-button type="danger" @click="vacuumDb" style="margin-left: 10px;">
                <DeleteFilled /> تنظيف (VACUUM)
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>التصور</h3>
          </template>
          <el-form :model="vizSettings" label-width="140px">
            <el-form-item label="تمكين العرض ثنائي الأبعاد">
              <el-switch v-model="vizSettings.enable_2d" active-text="مفعل" inactive-text="معطل" />
            </el-form-item>
            <el-form-item label="تمكين العرض ثلاثي الأبعاد">
              <el-switch v-model="vizSettings.enable_3d" active-text="مفعلة" inactive-text="معطلة" @change="on3dToggle" />
            </el-form-item>
            <el-form-item label="تكرار التحديث (Hz)">
              <el-input-number v-model="vizSettings.update_freq" :min="1" :max="120" style="width: 100%" />
            </el-form-item>
            <el-form-item label="طول المسار">
              <el-input-number v-model="vizSettings.trail_length" :min="0" :max="5000" style="width: 100%" />
            </el-form-item>
            <el-form-item label="إظهار عدم اليقين">
              <el-switch v-model="vizSettings.show_uncertainty" active-text="نعم" inactive-text="لا" />
            </el-form-item>
            <el-form-item label="نظام الإحداثيات">
              <el-select v-model="vizSettings.coordinate_system" style="width: 100%">
                <el-option label="ENU (شرق-شمال-أعلى)" value="ENU" />
                <el-option label="ECEF" value="ECEF" />
                <el-option label="LLA" value="LLA" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>التسجيل</h3>
          </template>
          <el-form :model="logSettings" label-width="120px">
            <el-form-item label="مستوى السجل">
              <el-select v-model="logSettings.level" style="width: 100%">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
              </el-select>
            </el-form-item>
            <el-form-item label="مجلد السجلات">
              <el-input v-model="logSettings.directory" placeholder="logs" style="width: 100%" />
            </el-form-item>
            <el-form-item label="الحد الأقصى لحجم الملف (بايت)">
              <el-input-number v-model="logSettings.max_bytes" :min="102400" :max="104857600" :step="102400" style="width: 100%" />
            </el-form-item>
            <el-form-item label="عدد الملفات المحفوظة">
              <el-input-number v-model="logSettings.backup_count" :min="1" :max="20" style="width: 100%" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>التقارير</h3>
          </template>
          <el-form :model="reportSettings" label-width="120px">
            <el-form-item label="مجلد الإخراج">
              <el-input v-model="reportSettings.output_dir" placeholder="reports" style="width: 100%" />
            </el-form-item>
            <el-form-item label="تنسيقات التصدير">
              <el-checkbox-group v-model="reportSettings.formats">
                <el-checkbox label="JSON" value="json" />
                <el-checkbox label="CSV" value="csv" />
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="تضمين البيانات الوصفية">
              <el-switch v-model="reportSettings.include_metadata" active-text="نعم" inactive-text="لا" />
            </el-form-item>
            <el-form-item label="ضغط الملفات">
              <el-switch v-model="reportSettings.compress" active-text="نعم" inactive-text="لا" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>الأمان والسلامة</h3>
          </template>
          <el-form :model="safetySettings" label-width="160px">
            <el-form-item label="فرض حدود المحاكاة">
              <el-switch v-model="safetySettings.enforce_boundary" active-text="مفعل" inactive-text="معطل" />
            </el-form-item>
            <el-form-item label="تصنيف جميع البيانات كمحاكاة">
              <el-switch v-model="safetySettings.label_simulated" active-text="مفعل" inactive-text="معطل" />
            </el-form-item>
            <el-form-item label="حظر الوصول الشبكي">
              <el-switch v-model="safetySettings.prohibit_network" active-text="مفعل" inactive-text="معطل" />
            </el-form-item>
            <el-form-item label="التحقق من الاستيراد">
              <el-switch v-model="safetySettings.validate_imports" active-text="مفعل" inactive-text="لا" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <h3>حفظ الإعدادات</h3>
          </template>
          <div class="save-actions">
            <el-button type="primary" @click="saveAllSettings" :loading="saving" size="large">
              <Download /> حفظ جميع الإعدادات
            </el-button>
            <el-button @click="resetToDefaults" style="margin-left: 16px;">
              <Refresh /> استعادة القيم الافتراضية
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh, Connection, Check } from '@element-plus/icons-vue'

const saving = ref(false)

const generalSettings = reactive({
  language: 'ar',
  theme: 'dark',
  debug: false
})

const simulationSettings = reactive({
  default_seed: 42,
  max_duration: 3600,
  max_objects: 1000,
  max_sensors: 100,
  max_observations: 100000,
  max_events: 10000,
  default_timestep: 0.1
})

const dbSettings = reactive({
  path: 'data/nados.db',
  echo: false,
  pool_size: 5,
  max_overflow: 10
})

const vizSettings = reactive({
  enable_2d: true,
  enable_3d: false,
  update_freq: 30,
  trail_length: 100,
  show_uncertainty: true,
  coordinate_system: 'ENU'
})

const logSettings = reactive({
  level: 'INFO',
  directory: 'logs',
  max_bytes: 10485760,
  backup_count: 5
})

const reportSettings = reactive({
  output_dir: 'reports',
  formats: ['json', 'csv'],
  include_metadata: true,
  compress: false
})

const safetySettings = reactive({
  enforce_boundary: true,
  label_simulated: true,
  prohibit_network: true,
  validate_imports: true
})

const saveAllSettings = async () => {
  saving.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('تم حفظ جميع الإعدادات بنجاح')
  } catch (error) {
    ElMessage.error(`فشل الحفظ: ${error.message}`)
  } finally {
    saving.value = false
  }
}

const resetToDefaults = () => {
  ElMessageBox.confirm('هل تريد استعادة جميع الإعدادات إلى القيم الافتراضية؟', 'تأكيد', {
    confirmButtonText: 'نعم',
    cancelButtonText: 'لا',
    type: 'warning'
  }).then(() => {
    ElMessage.info('تم استعادة القيم الافتراضية')
  })
}
</script>

<style scoped>
.settings-view {
  padding: 20px 0;
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

:deep(.el-checkbox-group) {
  display: flex;
  gap: 16px;
}

:deep(.el-checkbox__label) {
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
</style>