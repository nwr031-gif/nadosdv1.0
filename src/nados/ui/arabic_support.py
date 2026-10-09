"""
Arabic language support for UI.
"""

import os

# Arabic translations for UI elements
ARABIC_TRANSLATIONS: dict[str, str] = {
    # Application
    "app_name": "نظام نادوس للبحوث والمحاكاة",
    "app_version": "الإصدار 1.0.0",
    # Main window
    "main_title": "مركز القيادة والسيطرة - محاكاة الدفاع الجوي",
    "simulation_status": "حالة المحاكاة",
    "current_scenario": "السيناريو الحالي",
    "simulation_clock": "ساعة المحاكاة",
    # Controls
    "start_simulation": "تشغيل المحاكاة",
    "pause_simulation": "إيقاف مؤقت",
    "resume_simulation": "استئناف",
    "stop_simulation": "إيقاف",
    "reset_simulation": "إعادة ضبط",
    "select_scenario": "اختيار سيناريو",
    "simulation_speed": "سرعة المحاكاة",
    # Navigation
    "home": "الرئيسية",
    "view_2d": "المشهد ثنائي الأبعاد",
    "view_3d": "المشهد ثلاثي الأبعاد",
    "virtual_sensors": "المستشعرات الافتراضية",
    "object_tracking": "تتبع الأجسام",
    "event_log": "سجل الأحداث",
    "reports": "التقارير",
    "tests": "الاختبارات",
    "settings": "الإعدادات",
    # Dashboard
    "active_objects": "الأجسام النشطة",
    "valid_observations": "الملاحظات الصحيحة",
    "active_tracks": "المسارات النشطة",
    "dropout_rate": "معدل التساقط",
    "false_alarms": "الإنذارات الكاذبة",
    "avg_latency": "زمن الاستجابة المتوسط",
    "simulation_runtime": "زمن تشغيل المحاكاة",
    "cpu_usage": "استخدام المعالج",
    "memory_usage": "استخدام الذاكرة",
    "database_status": "حالة قاعدة البيانات",
    "system_health": "صحة النظام",
    # Simulation view
    "schematic_map": "الخريطة التخطيطية",
    "sensor_locations": "مواقع المستشعرات",
    "object_positions": "مواقع الأجسام",
    "estimated_tracks": "المسارات المقدرة",
    "object_ids": "معرفات الأجسام",
    "position_velocity": "الموقع والسرعة",
    "track_uncertainty": "عدم اليقين في المسار",
    "historical_trails": "المسارات التاريخية",
    "object_details": "تفاصيل الجسم",
    # Scenario editor
    "create_scenario": "إنشاء سيناريو",
    "scenario_name": "اسم السيناريو",
    "scenario_description": "وصف السيناريو",
    "duration": "المدة (ثواني)",
    "timestep": "خطوة الوقت (ثواني)",
    "random_seed": "بذرة العشوائية",
    "add_object": "إضافة جسم",
    "add_sensor": "إضافة مستشعر",
    "save_scenario": "حفظ السيناريو",
    "load_scenario": "تحميل سيناريو",
    "validate_scenario": "التحقق من السيناريو",
    # Results viewer
    "run_history": "تاريخ التشغيل",
    "scenario_comparison": "مقارنة السيناريوهات",
    "time_series_charts": "الرسوم البيانية الزمنية",
    "observation_vs_estimate": "الملاحظات مقابل التقديرات",
    "error_summary": "ملخص الأخطاء",
    "export_report": "تصدير التقرير",
    # Events
    "event_type": "نوع الحدث",
    "timestamp": "الطابع الزمني",
    "severity": "الخطورة",
    "message": "الرسالة",
    "source": "المصدر",
    # Status
    "running": "قيد التشغيل",
    "paused": "متوقف مؤقتاً",
    "stopped": "متوقف",
    "completed": "مكتمل",
    "error": "خطأ",
    "idle": "جاهز",
    # Severity
    "info": "معلومات",
    "warning": "تحذير",
    "critical": "حرج",
    # Messages
    "simulation_started": "تم بدء المحاكاة",
    "simulation_paused": "تم إيقاف المحاكاة مؤقتاً",
    "simulation_resumed": "تم استئناف المحاكاة",
    "simulation_stopped": "تم إيقاف المحاكاة",
    "simulation_reset": "تم إعادة ضبط المحاكاة",
    "simulation_completed": "اكتملت المحاكاة",
    "scenario_loaded": "تم تحميل السيناريو",
    "scenario_saved": "تم حفظ السيناريو",
    "report_generated": "تم إنشاء التقرير",
    "database_connected": "قاعدة البيانات متصلة",
    "database_error": "خطأ في قاعدة البيانات",
    # 3D View
    "toggle_3d": "تبديل العرض ثلاثي الأبعاد",
    "camera_controls": "تحكم الكاميرا",
    "orbit": "تدوير",
    "pan": "تحريك",
    "zoom": "تكبير/تصغير",
    "reset_view": "إعادة تعيين العرض",
    "show_axes": "إظهار المحاور",
    "show_grid": "إظهار الشبكة",
    "simulation_label": "محاكاة",
    # Settings
    "language": "اللغة",
    "theme": "السمة",
    "database_path": "مسار قاعدة البيانات",
    "log_level": "مستوى السجل",
    "max_duration": "أقصى مدة",
    "max_objects": "أقصى عدد أجسام",
    "enable_3d": "تمكين العرض ثلاثي الأبعاد",
    # Validation
    "validation_passed": "التحقق نجح",
    "validation_failed": "التحقق فشل",
    "invalid_scenario": "سيناريو غير صالح",
    "missing_required_field": "حقل مطلوب مفقود",
    "invalid_numeric_value": "قيمة رقمية غير صالحة",
}


def setup_arabic_support(app) -> None:
    """Set up Arabic RTL support for Qt application."""
    from PyQt6.QtCore import Qt

    # Set application layout direction to RTL
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # Set default font for Arabic
    from PyQt6.QtGui import QFont, QFontDatabase

    # Try to load Noto Sans Arabic
    font_families = QFontDatabase.families()
    arabic_font = None

    for family in ["Noto Sans Arabic", "Amiri", "Scheherazade", "Arial", "Tahoma"]:
        if family in font_families:
            arabic_font = family
            break

    if arabic_font:
        font = QFont(arabic_font, 10)
        app.setFont(font)

    # Set environment for proper Arabic shaping
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


def translate_ui(key: str, default: str = "") -> str:
    """Translate a UI key to Arabic."""
    return ARABIC_TRANSLATIONS.get(key, default)


def get_all_translations() -> dict[str, str]:
    """Get all translations dictionary."""
    return ARABIC_TRANSLATIONS.copy()
