<template>
  <div class="home-view">
    <!-- Welcome Section -->
    <el-row :gutter="20" class="welcome-section">
      <el-col :span="12">
        <el-card class="welcome-card">
          <template #header>
            <div class="card-header">
              <h2>مرحباً بك في نظام نادوس</h2>
              <el-tag type="danger" effect="dark">Dv1.0</el-tag>
            </div>
          </template>
          <div class="welcome-content">
            <p class="description">
              نظام نادوس للبحوث والمحاكاة (NADOS Dv1.0) هو بيئة متكاملة لمحاكاة 
              وتتبع الأجسام الجوية باستخدام مستشعرات افتراضية متعددة.
            </p>
            <div class="features">
              <el-descriptions border>
                <el-descriptions-item label="محاكاة حتمية">بذور عشوائية ثابتة للتكرار الدقيق</el-descriptions-item>
                <el-descriptions-item label="مستشعرات متعددة">رادار، ليدار، بصري، IRST</el-descriptions-item>
                <el-descriptions-item label="تتبع كالمّان">مرشح كالمّان بـ 9 حالات</el-descriptions-item>
                <el-descriptions-item label="دمج البيانات">تقاطع مصفوفات التباين (CI)</el-descriptions-item>
                <el-descriptions-item label="تصور ثنائي/ثلاثي الأبعاد">PyQt6 / Panda3D</el-descriptions-item>
                <el-descriptions-item label="قاعدة بيانات">SQLite مع SQLAlchemy</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="status-card">
          <template #header>
            <h3>حالة النظام</h3>
          </template>
          <div class="status-grid">
            <el-card class="stat-card">
              <div class="stat-icon"><Monitor /></div>
              <div class="stat-info">
                <div class="stat-value">{{ simulationStore.isConnected ? 'متصل' : 'غير متصل' }}</div>
                <div class="stat-label">قاعدة البيانات</div>
              </div>
            </el-card>
            <el-card class="stat-card">
              <div class="stat-icon"><Cpu /></div>
              <div class="stat-info">
                <div class="stat-value">{{ simulationStore.status }}</div>
                <div class="stat-label">حالة المحاكاة</div>
              </div>
            </el-card>
            <el-card class="stat-card">
              <div class="stat-icon"><Location /></div>
              <div class="stat-info">
                <div class="stat-value">{{ Object.keys(simulationStore.objects).length }}</div>
                <div class="stat-label">الأجسام النشطة</div>
              </div>
            </el-card>
            <el-card class="stat-card">
              <div class="stat-icon"><RadarIcon /></div>
              <div class="stat-info">
                <div class="stat-value">{{ Object.keys(simulationStore.sensors).length }}</div>
                <div class="stat-label">المستشعرات</div>
              </div>
            </el-card>
            <el-card class="stat-card">
              <div class="stat-icon"><Connection /></div>
              <div class="stat-info">
                <div class="stat-value">{{ Object.keys(simulationStore.tracks).length }}</div>
                <div class="stat-label">المسارات النشطة</div>
              </div>
            </el-card>
            <el-card class="stat-card">
              <div class="stat-icon"><Clock /></div>
              <div class="stat-info">
                <div class="stat-value">{{ simulationStore.formattedTime }}</div>
                <div class="stat-label">زمن المحاكاة</div>
              </div>
            </el-card>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Actions -->
    <el-row :gutter="20" class="actions-section">
      <el-col :span="24">
        <el-card>
          <template #header>
            <h3>إجراءات سريعة</h3>
          </template>
          <div class="actions-grid">
            <el-button type="primary" size="large" @click="goToSimulation" :disabled="simulationStore.isRunning">
              <Monitor /> الانتقال للمشهد
            </el-button>
            <el-button type="success" size="large" @click="goToScenarioEditor">
              <Edit /> إنشاء سيناريو جديد
            </el-button>
            <el-button type="info" size="large" @click="goToSensors">
              <RadarIcon /> إدارة المستشعرات
            </el-button>
            <el-button type="warning" size="large" @click="goToReports">
              <DocumentCopy /> عرض التقارير
            </el-button>
            <el-button type="primary" size="large" @click="runTests">
              <Checked /> تشغيل الاختبارات
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Scenarios -->
    <el-row :gutter="20" class="scenarios-section">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header-flex">
              <h3>السيناريوهات المتاحة</h3>
              <el-button type="text" @click="goToScenarioEditor">عرض الكل <ArrowRight /></el-button>
            </div>
          </template>
          <el-table :data="demoScenarios" border stripe style="width: 100%">
            <el-table-column prop="name" label="الاسم" width="200" />
            <el-table-column prop="description" label="الوصف" />
            <el-table-column prop="duration" label="المدة (ث)" width="100" />
            <el-table-column prop="objects" label="الأجسام" width="80" />
            <el-table-column prop="sensors" label="المستشعرات" width="100" />
            <el-table-column prop="seed" label="بذرة العشوائية" width="120" />
            <el-table-column label="الإجراءات" width="180">
              <template #default="scope">
                <el-button size="small" type="primary" @click="loadScenario(scope.row.id)">
                  <Monitor /> تحميل
                </el-button>
                <el-button size="small" @click="editScenario(scope.row.id)">
                  <Edit />
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulationStore } from '@/stores/simulation'
import { ElMessage } from 'element-plus'
import {
  Monitor, Cpu, Connection, Clock, DocumentCopy, Checked,
  Edit, ArrowRight, Aim as RadarIcon, Location
} from '@element-plus/icons-vue'

const router = useRouter()
const simulationStore = useSimulationStore()

const demoScenarios = [
  {
    id: 'basic_tracking',
    name: 'تتبع أساسي',
    description: 'جسم واحد مع مستشعر رادار بقياسات نظيفة',
    duration: 60,
    objects: 1,
    sensors: 1,
    seed: 42
  },
  {
    id: 'noisy_sensor',
    name: 'مستشعر ضوضائي',
    description: 'قياسات مع ضوضاء وتصفية كالمّان',
    duration: 120,
    objects: 1,
    sensors: 1,
    seed: 12345
  },
  {
    id: 'multi_sensor_demo',
    name: 'متعدد المستشعرات',
    description: 'دمج بيانات من 3 مستشعرات (راداران + ليدار)',
    duration: 180,
    objects: 1,
    sensors: 3,
    seed: 98765
  }
]

const goToSimulation = () => router.push('/simulation')
const goToScenarioEditor = () => router.push('/scenario-editor')
const goToSensors = () => router.push('/sensors')
const goToReports = () => router.push('/reports')
const goToTests = () => router.push('/tests')

const loadScenario = async (scenarioId) => {
  try {
    await simulationStore.loadScenario(scenarioId)
    router.push('/simulation')
    ElMessage.success(`تم تحميل السيناريو: ${scenarioId}`)
  } catch (error) {
    ElMessage.error(`فشل التحميل: ${error.message}`)
  }
}

const editScenario = (scenarioId) => {
  router.push({ path: '/scenario-editor', query: { edit: scenarioId } })
}

const runTests = async () => {
  router.push('/tests')
}
</script>

<style scoped>
.home-view {
  padding: 20px 0;
}

.welcome-section {
  margin-bottom: 20px;
}

.welcome-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h2 {
  margin: 0;
  color: #eaeaea;
}

.welcome-content .description {
  color: #aaa;
  line-height: 1.6;
  margin-bottom: 20px;
}

.status-card {
  height: 100%;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
  border: 1px solid #0f3460;
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(233, 69, 96, 0.2);
}

.stat-icon {
  font-size: 28px;
  color: #e94560;
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
  margin-top: 4px;
}

.actions-section {
  margin-bottom: 20px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.actions-grid .el-button {
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}

.actions-grid .el-button .el-icon {
  font-size: 24px;
}

.scenarios-section {
  margin-bottom: 20px;
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header-flex h3 {
  margin: 0;
  color: #eaeaea;
}

.card-header-flex .el-button--text {
  color: #e94560;
}

.card-header-flex .el-button--text:hover {
  color: #d63a55;
}

:deep(.el-table) {
  background: #16213e;
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

@media (max-width: 768px) {
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>