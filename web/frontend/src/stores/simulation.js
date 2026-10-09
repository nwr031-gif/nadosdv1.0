import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useSimulationStore = defineStore('simulation', () => {
  // State
  const status = ref('idle')
  const currentScenario = ref(null)
  const simulationTime = ref(0)
  const simulationDuration = ref(0)
  const simulationSpeed = ref(1.0)
  const progress = ref(0)
  const objects = ref({})
  const sensors = ref({})
  const tracks = ref({})
  const selectedObject = ref(null)
  const isConnected = ref(false)
  const lastError = ref(null)

  // Getters
  const isRunning = computed(() => status.value === 'running')
  const isPaused = computed(() => status.value === 'paused')
  const canStart = computed(() => status.value === 'idle' || status.value === 'stopped')
  const canPause = computed(() => status.value === 'running')
  const canResume = computed(() => status.value === 'paused')
  const canStop = computed(() => status.value === 'running' || status.value === 'paused')
  const canReset = computed(() => status.value !== 'idle')
  const formattedTime = computed(() => {
    const t = simulationTime.value
    const m = Math.floor(t / 60)
    const s = Math.floor(t % 60)
    const ms = Math.floor((t % 1) * 100)
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`
  })

  // Actions
  async function fetchStatus() {
    try {
      const [statusRes, objectsRes, sensorsRes, tracksRes] = await Promise.all([
        api.get('/simulation/status'),
        api.get('/simulation/objects').catch(() => ({ data: { objects: {} } })),
        api.get('/simulation/sensors').catch(() => ({ data: { sensors: {} } })),
        api.get('/simulation/tracks').catch(() => ({ data: { tracks: {} } })),
      ])
      updateState(statusRes.data)
      objects.value = objectsRes.data.objects || {}
      sensors.value = sensorsRes.data.sensors || {}
      tracks.value = tracksRes.data.tracks || {}
      isConnected.value = true
      lastError.value = null
    } catch (error) {
      isConnected.value = false
      lastError.value = error.message
      console.error('Failed to fetch simulation status:', error)
    }
  }

  function updateState(data) {
    if (data.status !== undefined) status.value = data.status
    if (data.current_time !== undefined) simulationTime.value = data.current_time
    if (data.duration !== undefined) simulationDuration.value = data.duration
    if (data.speed !== undefined) simulationSpeed.value = data.speed
    if (data.progress !== undefined) progress.value = data.progress
    if (data.objects !== undefined) objects.value = data.objects
    if (data.sensors !== undefined) sensors.value = data.sensors
    if (data.tracks !== undefined) tracks.value = data.tracks
  }

  async function startSimulation() {
    try {
      const response = await api.post('/simulation/start')
      updateState(response.data)
      return response.data
    } catch (error) {
      lastError.value = error.message
      throw error
    }
  }

  async function pauseSimulation() {
    try {
      const response = await api.post('/simulation/pause')
      updateState(response.data)
      return response.data
    } catch (error) {
      lastError.value = error.message
      throw error
    }
  }

  async function resumeSimulation() {
    try {
      const response = await api.post('/simulation/resume')
      updateState(response.data)
      return response.data
    } catch (error) {
      lastError.value = error.message
      throw error
    }
  }

  async function stopSimulation() {
    try {
      const response = await api.post('/simulation/stop')
      updateState(response.data)
      return response.data
    } catch (error) {
      lastError.value = error.message
      throw error
    }
  }

  async function resetSimulation() {
    try {
      const response = await api.post('/simulation/reset')
      updateState(response.data)
      selectedObject.value = null
      return response.data
    } catch (error) {
      lastError.value = error.message
      throw error
    }
  }

  async function setSpeed(speed) {
    try {
      const response = await api.post('/simulation/speed', { speed })
      simulationSpeed.value = response.data.speed
      return response.data
    } catch (error) {
      lastError.value = error.message
      throw error
    }
  }

  async function loadScenario(scenarioId) {
    try {
      const response = await api.post('/simulation/load', { scenario_id: scenarioId })
      currentScenario.value = response.data.scenario
      updateState(response.data)
      selectedObject.value = null
      return response.data
    } catch (error) {
      lastError.value = error.message
      throw error
    }
  }

  function selectObject(objectId) {
    selectedObject.value = objectId
  }

  function clearSelection() {
    selectedObject.value = null
  }

  // Start polling for status updates
  let pollInterval = null
  
  function startPolling(interval = 1000) {
    if (pollInterval) clearInterval(pollInterval)
    pollInterval = setInterval(fetchStatus, interval)
  }
  
  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  return {
    // State
    status,
    currentScenario,
    simulationTime,
    simulationDuration,
    simulationSpeed,
    progress,
    objects,
    sensors,
    tracks,
    selectedObject,
    isConnected,
    lastError,
    // Getters
    isRunning,
    isPaused,
    canStart,
    canPause,
    canResume,
    canStop,
    canReset,
    formattedTime,
    // Actions
    fetchStatus,
    updateState,
    startSimulation,
    pauseSimulation,
    resumeSimulation,
    stopSimulation,
    resetSimulation,
    setSpeed,
    loadScenario,
    selectObject,
    clearSelection,
    startPolling,
    stopPolling
  }
})